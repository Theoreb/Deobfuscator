import esprima
import escodegen
import os
import threading
from esprima.nodes import *
import jsbeautifier

from visitor import VisitorClass, VisitorTask, Task
from local import Model

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
        self.visitor = VisitorClass(self.ast)
        self.model: Model = Model()

    def save(self, output: str, file: str):
        with open(os.path.join(self.output_folder, file), 'w') as file:
            file.write(output)

    def save_thread(self, file: str):
        threading.Thread(target=self.save, args=(escodegen.generate(self.visitor.ast), file)).start()

    def desobfuscate(self) -> str:
        identifiers = self.visitor.process(VisitorTask(Task.INIT))

        completed = 0
        total_count = len([el for element in identifiers.values() for el in element])
        print(f"Total count: {total_count}")

        print(identifiers.keys())

        for id in identifiers.keys():
            for decl_node, id_type in identifiers[id]:

                bprint(f"[bold blue][SEARCH {repr(id)}][/]: Searching context for {id_type.value}: {id} in Node of type: {decl_node.type if decl_node else None}")
                context = self.visitor.process(VisitorTask(Task.CONTEXT, id, 14000), decl_node)
                context = "\n\n\n".join(context)[:14000]
                bprint(f"[bold blue][CONTEXT {repr(id)}][/]: Found context (len: {len(context)} chars)")
                
                print(context)

                renamed = ''
                self.model.clear()
                while not renamed or (renamed != id and renamed in identifiers.keys()):
                    description, renamed, response = self.model.generate(id, context, id_type)

                    bprint(f"[bold green][MODEL {repr(id)}][/]")
                    print(f"[Description]: {description}")
                    bprint(f"[bold green][MODEL]: {repr(id)} Renamed to {repr(renamed)}[/] ({repr(response)})")
                    if (renamed != id and renamed in identifiers.keys()):
                        bprint(f"[bold red][MODEL {repr(id)}][/]: {repr(renamed)} Already declared in the code !",)
                        self.model.add_already(id, renamed)

                self.visitor.process(VisitorTask(Task.APPLY, id, renamed, id_type), decl_node)
                
                completed += 1

                # Print progress
                bprint(f"[bold yellow][Progress][/]: {completed} / {total_count} ({completed / total_count * 100:.2f}%)")
                self.save_thread(f'deobfuscated.js')
        
        self.save(jsbeautifier.beautify(escodegen.generate(self.visitor.ast)), 'deobfuscated.js')