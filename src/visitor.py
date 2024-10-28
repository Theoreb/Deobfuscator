from esprima.nodes import *
from typing import Callable

import escodegen

class Scope:
    def __init__(self, parent = None, node = None):
        self.parent: Scope = parent
        self.node: Node = node
        self.declared = set()
        self.children: list[Scope] = []

    def __repr__(self, depth: int = 0):
        text = f"{'  ' * depth}Scope(declared={self.declared}:"
        for child in self.children:
            text += f"\n{child.__repr__(depth + 1)}"
        return text
    
    def __iter__(self):
        for child in self.children:
            yield from child

    def count_declared(self) -> int:
        total = len(self.declared)
        for child in self.children:
            total += child.count_declared()
        return total
    
    def get_parent_defined(self, var: str) -> bool:
        if var in self.declared:
            return True
        if self.parent:
            return self.parent.get_parent_defined(var)
        return False

    def change_name(self, visitor: 'Visitor', old_name: str, new_name: str):
        if old_name not in self.declared:
            print(f"Variable '{old_name}' not declared in scope")
            if self.parent:
                self.parent.change_name(visitor, old_name, new_name)
                return
            
        while self.get_parent_defined(new_name):
            new_name = "_" + new_name
        
        if new_name in self.declared:
            new_name = "_" + new_name
            while self.get_parent_defined(new_name):
                new_name = "_" + new_name
        
        # Rename in declared and used lists
        if old_name in self.declared:
            self.declared.remove(old_name)
            self.declared.add(new_name)
        
        # Define the task to rename identifiers in the AST
        def task(node: Node, scope: Scope):
            if old_name in scope.declared:
                return
            if node.type == Syntax.Identifier and node.name == old_name:
                node.name = new_name

        # Set the task and visit the nodes in this scope
        visitor.set_task(task)
        visitor.visit(self)

    def replace_ast(self, visitor: 'Visitor', new_ast: Script):
        self.node = new_ast.body[0]

    def get_code(self) -> str:
        return escodegen.generate(self.node)

    def get_context(self, visitor: 'Visitor', limit: int, var: str) -> str:
        code: str = escodegen.generate(self.node)
        if len(code) <= limit:
            return code

        # Trouver toutes les positions des occurrences de la variable 'var' dans le code
        occurrences = []
        index = code.find(var)
        while index != -1:
            occurrences.append(index)
            index = code.find(var, index + len(var))

        if not occurrences:
            return ""  # La variable n'est pas présente dans le code

        # Regrouper les occurrences proches en clusters
        clusters = []
        cluster = [occurrences[0]]
        for i in range(1, len(occurrences)):
            if occurrences[i] - occurrences[i - 1] <= 50:  # Seuil de proximité (ajustable)
                cluster.append(occurrences[i])
            else:
                clusters.append(cluster)
                cluster = [occurrences[i]]
        clusters.append(cluster)  # Ajouter le dernier cluster

        # Générer les fragments autour de chaque cluster
        fragments = []
        total_length = 0
        max_fragment_size = limit // len(clusters)  # Taille maximale par fragment

        for cluster in clusters:
            # Déterminer les bornes du fragment pour le cluster
            start = cluster[0]
            end = cluster[-1] + len(var)

            # Étendre le fragment pour ajouter du contexte, sans dépasser les limites
            context_size = (max_fragment_size - (end - start)) // 2
            context_size = max(context_size, 30)  # Contexte minimum de 30 caractères de chaque côté

            fragment_start = max(0, start - context_size)
            fragment_end = min(len(code), end + context_size)

            fragment = code[fragment_start:fragment_end]

            fragment_length = len(fragment)
            if total_length + fragment_length > limit:
                # Si ajouter ce fragment dépasse la limite, on doit ajuster la taille
                available_length = limit - total_length
                if available_length <= 0:
                    break  # Plus d'espace disponible
                fragment = fragment[:available_length]
                fragments.append(fragment)
                total_length += len(fragment)
                break
            else:
                fragments.append(fragment)
                total_length += fragment_length

        # Combiner les fragments avec des séparateurs
        return "\n[...]\n".join(fragments)

class Visitor:
    def __init__(self, ast: Script):
        self.ast: Script = ast
        self.current_task: Callable = lambda node, scope: None
        self.global_scope = Scope(node=self.ast)
        self.current_scope = self.global_scope

        # First pass to build the scope tree
        self.initialized = False
        self.visit_node(self.ast)
        self.initialized = True

    def enter_scope(self, node: Node):
        if node == self.current_scope.node:
            return
        for child in self.current_scope.children:
            if child.node == node:
                self.current_scope = child
                return
        new_scope = Scope(parent=self.current_scope, node=node)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
        else:
            self.current_scope = None

    def declare_identifier(self, name: str):
        if not self.initialized:
            self.current_scope.declared.add(name)

    def set_task(self, task: Callable = lambda node, scope: None):
        self.current_task = task

    def visit(self, scope: Scope = None):
        if scope is None:
            scope = self.global_scope
        node = scope.node
        self.current_scope = scope
        self.visit_node(node)

    def visit_node(self, node: Node, scope: bool = False):
        self.current_task(node, self.current_scope)
        match node.type:
            case Syntax.Program:
                for body in node.body:
                    self.visit_node(body)
            case Syntax.Identifier:
                pass

            case Syntax.VariableDeclarator:
                if node.id.type == Syntax.Identifier:
                    self.declare_identifier(node.id.name)

                self.visit_node(node.id)
                if node.init:
                    self.visit_node(node.init)

            case Syntax.ExpressionStatement:
                self.visit_node(node.expression)
            case Syntax.AssignmentExpression:
                self.visit_node(node.left)
                self.visit_node(node.right)
            case Syntax.MemberExpression:
                self.visit_node(node.object)
                self.visit_node(node.property)
            case Syntax.UnaryExpression:
                self.visit_node(node.argument)
            case Syntax.NewExpression:
                self.visit_node(node.callee)
                for arg in node.arguments:
                    assert arg
                    self.visit_node(arg)
            case Syntax.CallExpression:
                self.visit_node(node.callee)       
                for arg in node.arguments:
                    self.visit_node(arg)
            case Syntax.IfStatement:
                self.visit_node(node.test)
                self.visit_node(node.consequent)

                if node.alternate:
                    self.visit_node(node.alternate)
            case Syntax.VariableDeclaration:
                for decl in node.declarations:
                    assert decl
                    self.visit_node(decl)

            case Syntax.BlockStatement:
                if not scope:
                    self.enter_scope(node)
                for body in node.body:
                    self.visit_node(body)
                if not scope:
                    self.exit_scope()

            case Syntax.FunctionDeclaration:
                if node.id and node.id.type == Syntax.Identifier:
                    self.declare_identifier(node.id.name)
                    self.visit_node(node.id)

                self.enter_scope(node)
                for param in node.params:
                    if param.type == Syntax.Identifier:
                        self.declare_identifier(param.name)
                    self.visit_node(param)

                self.visit_node(node.body, scope=True)
                self.exit_scope()

            case Syntax.FunctionExpression | Syntax.ArrowFunctionExpression:
                self.enter_scope(node)

                for param in node.params:
                    if param.type == Syntax.Identifier:
                        self.declare_identifier(param.name)
                    self.visit_node(param)

                self.visit_node(node.body, scope=True)
                self.exit_scope()

            case Syntax.ClassDeclaration:
                if node.id and node.id.type == Syntax.Identifier:
                    self.declare_identifier(node.id.name)
                    self.visit_node(node.id)

                if node.body:
                    self.visit_node(node.body)

            case Syntax.ClassExpression:
                if node.id and node.id.type == Syntax.Identifier:
                    self.declare_identifier(node.id.name)
                    self.visit_node(node.id)

                if node.body:
                    self.visit_node(node.body)

            case Syntax.ClassBody:
                self.enter_scope(node)
                for element in node.body:
                    self.visit_node(element)
                self.exit_scope()

            case Syntax.MethodDefinition:
                if node.key:
                    self.visit_node(node.key)
                    self.declare_identifier(node.key.name)

                if node.value:
                    self.visit_node(node.value)


            case Syntax.ThisExpression:
                pass
            case Syntax.BinaryExpression:
                self.visit_node(node.left)
                self.visit_node(node.right)
            case Syntax.UpdateExpression:
                self.visit_node(node.argument)
            case Syntax.LogicalExpression:
                self.visit_node(node.left)
                self.visit_node(node.right)
            case Syntax.ReturnStatement:
                if node.argument:
                    self.visit_node(node.argument)

            case Syntax.WhileStatement | Syntax.DoWhileStatement:
                self.visit_node(node.test)
                self.visit_node(node.body)

            case Syntax.ForInStatement | Syntax.ForOfStatement:
                self.visit_node(node.left)
                self.visit_node(node.right)
                self.visit_node(node.body)

            case Syntax.ArrayExpression:
                for element in node.elements:
                    self.visit_node(element)
            case Syntax.ObjectExpression:
                for prop in node.properties:
                    self.visit_node(prop)
            case Syntax.Property:
                self.visit_node(node.key)
                self.visit_node(node.value)
            case Syntax.ConditionalExpression:
                self.visit_node(node.test)
                self.visit_node(node.consequent)
                if node.alternate:
                    self.visit_node(node.alternate)
            case Syntax.ArrayPattern:
                for element in node.elements:
                    self.visit_node(element)
            case Syntax.ObjectPattern:
                for prop in node.properties:
                    self.visit_node(prop)
            case Syntax.SpreadElement:
                self.visit_node(node.argument)
            case Syntax.AssignmentExpression:
                self.visit_node(node.left)
                self.visit_node(node.right)
            case Syntax.AssignmentPattern:
                self.visit_node(node.left)
                self.visit_node(node.right)

            case Syntax.ForStatement:
                if node.init:
                    self.visit_node(node.init)
                if node.test:
                    self.visit_node(node.test)
                if node.update:
                    self.visit_node(node.update)
                self.visit_node(node.body)

            case Syntax.TryStatement:
                self.visit_node(node.block)
                if node.handler:
                    self.visit_node(node.handler)
                if node.finalizer:
                    self.visit_node(node.finalizer)
            case Syntax.CatchClause:
                self.visit_node(node.param)
                self.visit_node(node.body)
            case Syntax.SwitchStatement:
                self.visit_node(node.discriminant)
                for case in node.cases:
                    self.visit_node(case)
            case Syntax.SwitchCase:
                if node.test:
                    self.visit_node(node.test)
                for consequent in node.consequent:
                    self.visit_node(consequent)
            case Syntax.BreakStatement:
                if node.label:
                    self.visit_node(node.label)
            case Syntax.ContinueStatement:
                if node.label:
                    self.visit_node(node.label)
            case Syntax.ReturnStatement:
                if node.argument:
                    self.visit_node(node.argument)
            case Syntax.WithStatement:
                self.visit_node(node.object)
            case Syntax.TaggedTemplateExpression:
                self.visit_node(node.tag)
                self.visit_node(node.quasi)
            case Syntax.MethodDefinition:
                if node.computed:
                    self.visit_node(node.computed)
                if node.value:
                    self.visit_node(node.value)
            case Syntax.TemplateLiteral:
                for expression in node.expressions:
                    self.visit_node(expression)
            case Syntax.TemplateElement:
                self.visit_node(node.value)
            case Syntax.MetaProperty:
                self.visit_node(node.meta)
            case Syntax.Literal:
                # Fix bugs in escodegen
                if isinstance(node.value, str):
                    # Escape inner double quotes
                    node.value = node.value.replace("'", '"')

            case Syntax.SequenceExpression:
                for expression in node.expressions:
                    self.visit_node(expression)
            case _:
                print(f"Type unknown: {node.type} from path {node.path}")