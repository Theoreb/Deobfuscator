import copy
import escodegen
from esprima.nodes import *
from enum import Enum
import random

class Task(Enum):
    INIT = 0
    CONTEXT = 1
    APPLY = 2

class IdentifierType(Enum):
    VAR = "variable"
    FUNC = "function"

class VisitorTask:
    def __init__(self, type: Task, *args):
        self.type = type

        if type == Task.CONTEXT:
            self.var: str = args[0]
            self.context_size: int = args[1]
            self.contexts: list = []
        elif type == Task.APPLY:
            self.changes: tuple = (args[0], args[1])
            self.change_type: str = args[2]
        elif type == Task.INIT:
            self.identifiers: dict = {}

def similar(str1: str, str2: str) -> bool:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio() > 0.6

class VisitorClass:
    def __init__(self, ast: Script):
        self.ast: Script = ast

    def process(self, task: VisitorTask, node: Node = None):
        if not node or (task.type == Task.APPLY and task.change_type == IdentifierType.FUNC):
            for bodyNode in self.ast.body:
                self.visit_node(bodyNode, task)
        else:
            self.visit_node(node, task)

        if task.type == Task.CONTEXT:
            return task.contexts
        elif task.type == Task.INIT:
            return task.identifiers
        
    def get_context(self, path: list[Node], task: VisitorTask):
        if len(task.contexts) >= task.context_size:
            return
        
        generated_code = ""
        index = 0
        for i in range(len(path) - 2, 0, -1):
            if path[i].type in [Syntax.FunctionDeclaration, Syntax.FunctionExpression]:
                index = i
                break
       
        # Gain Context
        generated_code = escodegen.generate(path[index], {'format': { 'indent': { 'style': '    ' }, 'newline': '\n' , 'space': ' ' }} )
        if not generated_code in task.contexts:
            task.contexts.append(generated_code)

    def visit_node(self, node: Node, task: VisitorTask, path: list[Node] = []):
        path = list(path + [node])

        depth = len(path)
        match node.type:
            case Syntax.ExpressionStatement:
                assert node.expression
                self.visit_node(node.expression, task, path)
            case Syntax.AssignmentExpression:
                assert node.left
                assert node.right
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
            case Syntax.MemberExpression:
                assert node.object
                assert node.property
                self.visit_node(node.object, task, path)
                self.visit_node(node.property, task, path)
            case Syntax.Identifier:
                if task.type == Task.APPLY:
                    if node.name == task.changes[0]:
                        # print(f"Renamed {node.name} to {task.changes[1]}")
                        node.name = task.changes[1]
                elif task.type == Task.CONTEXT:
                    if node.name == task.var:
                        ctx = self.get_context(path, task)
                        if ctx:
                            task.contexts.append(ctx)
            case Syntax.UnaryExpression:
                assert node.argument
                self.visit_node(node.argument, task, path)
            case Syntax.NewExpression:
                assert node.callee
                self.visit_node(node.callee, task, path)
                for arg in node.arguments:
                    assert arg
                    self.visit_node(arg, task, path)
            case Syntax.CallExpression:
                assert node.callee
                self.visit_node(node.callee, task, path)
                if task.type == Task.APPLY and node.callee.type is Syntax.Identifier:

                    if node.callee.name == task.changes[0] :
                        # print(f"Renamed {node.callee.name} to {task.changes[1]}")
                        node.callee.name = task.changes[1]
                        
                for arg in node.arguments:
                    assert arg

                    self.visit_node(arg, task, path)
            case Syntax.FunctionExpression:             
                for param in node.params:
                    assert param.type is Syntax.Identifier

                    if task.type == Task.APPLY and param.name == task.changes[0]:
                        if depth <= 1:
                            param.name = task.changes[1]
                        else:
                            # print(f"Refused to rename {param.name} because it is a parameter of a function and depth is {depth}")
                            return
                    elif task.type == Task.CONTEXT and param.name == task.var:
                        if depth <= 1:
                            self.get_context(path, task)
                        else:
                            # print(f"Refused to Context {param.name} because it is a parameter of a function and depth is {depth}")
                            return

                    elif task.type == Task.INIT:
                        if param.name not in task.identifiers.keys():
                            task.identifiers[param.name] = []
                        task.identifiers[param.name].append((node, IdentifierType.VAR))

                if node.body.type == Syntax.BlockStatement:
                    for body in node.body.body:
                        assert body
                        self.visit_node(body, task, path)
                else:
                    assert node.body
                    self.visit_node(node.body, task, path)
            case Syntax.IfStatement:
                assert node.test
                assert node.consequent
                self.visit_node(node.test, task, path)
                self.visit_node(node.consequent, task, path)

                if node.alternate:
                    assert node.alternate
                    self.visit_node(node.alternate, task, path)
            case Syntax.VariableDeclaration:
                for decl in node.declarations:
                    assert decl
                    self.visit_node(decl, task, path)
            case Syntax.BlockStatement:
                for body in node.body:
                    assert body
                    self.visit_node(body, task, path)
            case Syntax.VariableDeclarator:
                assert node.id
                self.visit_node(node.id, task, path)
                if node.init:
                    assert node.init
                    self.visit_node(node.init, task, path)

                if task.type == Task.INIT:
                    if node.id.name not in task.identifiers.keys():
                        task.identifiers[node.id.name] = []
                    
                    if len(path) < 3:
                        task.identifiers[node.id.name].append((None, IdentifierType.VAR))
                    else:
                        task.identifiers[node.id.name].append((path[-3], IdentifierType.VAR))

            case Syntax.FunctionDeclaration:                
                assert node.id
                self.visit_node(node.id, task, path)

                if task.type == Task.INIT:
                    if node.id.name not in task.identifiers.keys():
                        task.identifiers[node.id.name] = []
                    task.identifiers[node.id.name].append((node, IdentifierType.FUNC))
                elif task.type == Task.APPLY:
                    if node.id.name == task.changes[0]:
                        # print(f"Renamed {node.id.name} to {task.changes[1]}")
                        node.id.name = task.changes[1]
                
                if node.params:
                    for param in node.params:
                        assert param.type is Syntax.Identifier

                        if task.type == Task.APPLY and param.name == task.changes[0]:
                            if depth <= 1:
                                param.name = task.changes[1]
                            else:
                                # print(f"Refused to rename {param.name} because it is a parameter of a function and depth is {depth}")
                                return
                        elif task.type == Task.CONTEXT and param.name == task.var:
                            if depth <= 1:
                                self.get_context(path, task)
                            else:
                                # print(f"Refused to Context {param.name} because it is a parameter of a function and depth is {depth}")
                                return
                        elif task.type == Task.INIT:
                            if param.name not in task.identifiers.keys():
                                task.identifiers[param.name] = []
                            task.identifiers[param.name].append((node, IdentifierType.VAR))

                assert node.body
                self.visit_node(node.body, task, path)

            case Syntax.ThisExpression:
                pass
            case Syntax.BinaryExpression:
                assert node.left
                assert node.right
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
            case Syntax.UpdateExpression:
                assert node.argument
                self.visit_node(node.argument, task, path)
            case Syntax.LogicalExpression:
                assert node.left
                assert node.right
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
            case Syntax.ReturnStatement:
                if node.argument:
                    assert node.argument
                    self.visit_node(node.argument, task, path)
            case Syntax.WhileStatement:
                assert node.test
                assert node.body
                self.visit_node(node.test, task, path)
                self.visit_node(node.body, task, path)
            case Syntax.ArrayExpression:
                for element in node.elements:
                    assert element
                    self.visit_node(element, task, path)
            case Syntax.ObjectExpression:
                for prop in node.properties:
                    assert prop
                    self.visit_node(prop, task, path)
            case Syntax.Property:
                assert node.value
                self.visit_node(node.value, task, path)
            case Syntax.ConditionalExpression:
                assert node.test
                assert node.consequent
                self.visit_node(node.test, task, path)
                self.visit_node(node.consequent, task, path)

                if node.alternate:
                    assert node.alternate
                    self.visit_node(node.alternate, task, path)
            case Syntax.ArrayPattern:
                for element in node.elements:
                    assert element
                    self.visit_node(element, task, path)
            case Syntax.ObjectPattern:
                for prop in node.properties:
                    assert prop
                    self.visit_node(prop, task, path)
            case Syntax.ForInStatement:
                assert node.left
                assert node.right
                assert node.body
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
                self.visit_node(node.body, task, path)
            case Syntax.ForOfStatement:
                assert node.left
                assert node.right
                assert node.body
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
                self.visit_node(node.body, task, path)
            case Syntax.SpreadElement:
                assert node.argument
                self.visit_node(node.argument, task, path)
            case Syntax.AssignmentExpression:
                assert node.left
                assert node.right
                
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)

            case Syntax.AssignmentPattern:
                assert node.left
                assert node.right
                self.visit_node(node.left, task, path)
                self.visit_node(node.right, task, path)
            case Syntax.ClassDeclaration:
                assert node.id
                self.visit_node(node.id, task, path)
                if node.body:
                    assert node.body
                    self.visit_node(node.body, task, path)
            case Syntax.ClassExpression:
                assert node.id
                self.visit_node(node.id, task, path)
                if node.body:
                    assert node.body
                    self.visit_node(node.body, task, path)
            case Syntax.ClassBody:
                for body in node.body:
                    assert body
                    self.visit_node(body, task, path)
            case Syntax.ForStatement:
                assert node.body
                if node.init:
                    assert node.init
                    self.visit_node(node.init, task, path)
                if node.test:
                    self.visit_node(node.test, task, path)
                if node.update:
                    assert node.update
                    self.visit_node(node.update, task, path)
                self.visit_node(node.body, task, path)
            case Syntax.FunctionExpression:
                assert node.id
                self.visit_node(node.id, task, path)

                if task.type == Task.APPLY:
                    if node.id == task.changes[0]:
                        # print(f"Reidd {node.id} to {task.changes[1]}")
                        node.id = task.changes[1]

                if node.params:
                    for param in node.params:
                        assert param
                        self.visit_node(param, task, path)

                assert node.body
                self.visit_node(node.body, task, path)
            case Syntax.TryStatement:
                assert node.block
                self.visit_node(node.block, task, path)
                if node.handler:
                    assert node.handler
                    self.visit_node(node.handler, task, path)
                if node.finalizer:
                    assert node.finalizer
                    self.visit_node(node.finalizer, task, path)
            case Syntax.CatchClause:
                assert node.param
                self.visit_node(node.param, task, path)
                assert node.body
                self.visit_node(node.body, task, path)
            case Syntax.SwitchStatement:
                assert node.discriminant
                assert node.cases
                self.visit_node(node.discriminant, task, path)
                for case in node.cases:
                    assert case
                    self.visit_node(case, task, path)
            case Syntax.SwitchCase:
                assert node.consequent
                if node.test:
                    assert node.test
                    self.visit_node(node.test, task, path)
                for consequent in node.consequent:
                    assert consequent
                    self.visit_node(consequent, task, path)
            case Syntax.BlockStatement:
                for statement in node.body:
                    assert statement
                    self.visit_node(statement, task, path)
            case Syntax.BreakStatement:
                if node.label:
                    assert node.label
                    self.visit_node(node.label, task, path)
            case Syntax.ContinueStatement:
                if node.label:
                    assert node.label
                    self.visit_node(node.label, task, path)
            case Syntax.ReturnStatement:
                if node.argument:
                    assert node.argument
                    self.visit_node(node.argument, task, path)
            case Syntax.WithStatement:
                assert node.object
                assert node.body
                self.visit_node(node.object, task, path)
            case Syntax.TaggedTemplateExpression:
                assert node.tag
                assert node.quasi
                self.visit_node(node.tag, task, path)
                self.visit_node(node.quasi, task, path)
            case Syntax.MethodDefinition:
                assert node.key
                if node.computed:
                    assert node.computed
                    self.visit_node(node.computed, task, path)
                if node.value:
                    assert node.value
                    self.visit_node(node.value, task, path)
            case Syntax.TemplateLiteral:
                for expression in node.expressions:
                    assert expression
                    self.visit_node(expression, task, path)
            case Syntax.TemplateElement:
                assert node.value
                self.visit_node(node.value, task, path)
            case Syntax.MetaProperty:
                assert node.meta
                assert node.property
                self.visit_node(node.meta, task, path)
            case Syntax.ArrowFunctionExpression:
                assert node.body
                self.visit_node(node.body, task, path)
            case Syntax.Literal:
                if task.type == Task.INIT:
                    # Fix bugs in escodegen
                    if isinstance(node.value, str):
                        # Escape inner double quotes
                        node.value = node.value.replace("'", '"')

            case Syntax.SequenceExpression:
                for expression in node.expressions:
                    assert expression
                    self.visit_node(expression, task, path)
            case _:
                print(f"Type unknown: {node.type} from path {node.path}")