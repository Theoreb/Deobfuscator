import esprima
import escodegen
import os
import threading
from esprima.nodes import *
import jsbeautifier
import tqdm # type: ignore

from src.visitor import *
from src.local import Model

from rich import print as bprint

class Desobfuscator:
    def __init__(self, file: str):
        self.output_folder: str = "output"
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        else:
            for f in os.listdir(self.output_folder):
                os.remove(os.path.join(self.output_folder, f))

        self.program: str = ""
        with open(file, 'r') as file:
            self.program = file.read()

        self.ast: Script = esprima.parseScript(self.program)
        self.visitor = Visitor(self.ast)
        self.model: Model = Model()

        self.progress_bar = tqdm.tqdm(total=self.visitor.global_scope.count_declared())

    def save(self, output: str, file: str):
        with open(os.path.join(self.output_folder, file), 'w') as file:
            file.write(output)

        print(f"Saved {file}")

    def save_thread(self, file: str):
        threading.Thread(target=self.save, args=(escodegen.generate(self.visitor.ast), file)).start()

    def desobfuscate(self, scope: Scope = None) -> str:
        if not scope:
            self.save_thread(f"output.js")
            scope = self.visitor.global_scope
        
        code = scope.get_code()
        if len(code) > 1000000000:
            ast, changes = self.model.transform(code)
            for var, new_name in changes.items():
                scope.change_name(self.visitor, var, new_name)
            # scope.replace_ast(self.visitor, ast)
        else:
            print(f"Code too long: {len(code)} chars")
            for var in scope.declared:
                if len(var) >= 3: # Assuming no obfuscated names with more than 3 characters
                    continue

                context = scope.get_context(self.model, self.model.context_size, var)
                if context:
                    new_var = self.model.predict(var, context, scope.declared)
                    if new_var != var:
                        scope.change_name(self.visitor, var, new_var)

                    self.save_thread(f"output.js")

                    self.progress_bar.update(1)

                else:
                    print(f"Could not find context for {var}")

        for child in scope.children:
            self.desobfuscate(child)

        if scope == self.visitor.global_scope:
            return code