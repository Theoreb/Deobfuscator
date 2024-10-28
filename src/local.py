import ollama
import esprima
import re
import json

class Model:
    NOT_ALLOWED = [
        'function', 'while', 'for', 'if', 'else',
        'var', 'let', 'const', 'import', 'export',
        'true', 'false', 'null', 'undefined', 'default',
        'break', 'continue', 'return', 'async', 'await',
        'switch', 'case', 'throw', 'try', 'catch', 'finally'
    ]
    system_prompt: str = "You are a specialist in Javascript Desobfuscation."

    def __init__(self, model: str = 'llama3.2'):
        self.model = model
        self.context_size = 4096
        self.context: str = ""

    def clear_context(self):
        self.context = ""

    def generate(self, prompt: str, num_predict: int) -> str:
        stream = ollama.generate(self.model, prompt, system=self.system_prompt, options={'num_predict': num_predict, 'num_ctx': self.context_size}, stream=True)

        response = ''
        print("[LLM]")
        for chunk in stream:
            if chunk['done']:
                self.context = chunk['context']
                print(f"\nPrompt Size: {chunk['prompt_eval_count']} | Eval Count: {chunk['eval_count']}")
            data = chunk['response']
            response += data

            if re.search(r"\`\`\`([\s\S]*?)\`\`\`", response):
                print('stopping')
                break

            print(data, end='', flush=True)

        return response

    def transform(self, code):
        self.clear_context()
        prompt = f"Read the following Javascript code and recopy it while only changing the variable name to make them more readable and meaningful.\n\n```javascript{code}``` When done, give me a JSON object indicating all the variable names that have been changed in this format:\n\n```json\n{{'old_name': 'new_name', 'old_name2': 'new_name2', 'old_name3': 'new_name3'...}}\n```Make sure you haven't forgotten to include any names.\n\n"
        response = self.generate(prompt, len(code) + 500)
        transformed_code = response.split('```javascript')[1].split('```')[0]
        changes = response.split('```json')[1].split('```')[0]
        
        while True:
            try:
                ast = esprima.parseScript(transformed_code)
                break
            except esprima.Error as e:
                print("Parsing error:", e)
                prompt = f"This javascript code is not valid. Please rewrite it and fix the following error:\n\nError: {e}\n\n```javascript{transformed_code}```"
                response = self.generate(prompt, len(code) + 200)

                transformed_code = response.split('```javascript')[1].split('```')[0]
        
        while True:
            try:
                json.loads(changes)
                break
            except json.JSONDecodeError as e:
                print("JSON error:", e)
                prompt = f"This javascript code is not valid. Please rewrite it and fix the following error:\n\nError: {e}\n\n```javascript{changes}```"
                response = self.generate(prompt, len(code) + 200)

                transformed_code = response.split('```javascript')[1].split('```')[0]
        return ast, json.loads(changes)
    
    def predict(self, var: str, context: str, declared: set):
        self.clear_context()
        prompt = f"Given the following piece of code, predict the original name of the variable/function `{var}` before obfuscation. If the context is unclear, give me a name which is the more meaningful possible to make it more readable. However, many variables haven't been obfuscated: if the variable/function `{var}` make sense, return the same name.\n\nHere some examples where the variable/function `{var}` appears:\n\n```javascript{context}```\n\nDon't give multiple proposals. Make sure the new name isn't already used in the code. IMPORTANT: Summarize your response in this JSON format: \n\n```json\n{{'name': '<myNewName>'}}\n```"
        response = self.generate(prompt, 300)

        attempt = 0
        while True:
            try:
                if attempt > 6:
                    return "failedAttempt"
                attempt += 1
                if '```json' in response:
                    formated_response = response.split('```json')[1].split('```')[0].replace("'", '"')
                else:
                    formated_response = response.split('```')[1].split('```')[0].replace("'", '"')

                name = json.loads(formated_response)
                if isinstance(name, json.JSONDecodeError):
                    raise name
                if not 'name' in name:
                    raise ValueError(f"Name not found in response: {name}")
                if name.get('name', None) in declared and name.get('name', None) != var:
                    raise NameError(f"Name {name['name']} has been already declared")
                break
            except ValueError as e:
                print("JSON error:", e)
                prompt = f"Your JSON response is not valid. Please rewrite it in the format: \n```json\n{{'name': '<myNewName>'}}\n```Ensure you have specified the 'name' field.\nThe new name for the variable/function `{var}` need to be more meaningful and not already used in the code.\nAnd fix the following error:\nError: {e}\n\nHere is the code where the variable/function `{var}` appears:\n\n```\ncjavascript{context}\n```"
                response = self.generate(prompt, 50)
            except IndexError as e:
                print("Index error:", e)
                prompt = f"Your JSON response is not valid. Please rewrite it in the format: \n```json\n{{'name': '<myNewName>'}}\n```Ensure you have specified the 'name' field.\nThe new name for the variable/function `{var}` need to be more meaningful and not already used in the code.\n\nHere is the code where the variable/function `{var}` appears:\n\n```javascript\n{context}\n```"
                response = self.generate(prompt, 50)
            except NameError as e:
                print("Value error:", e)
                prompt = f"The name `{name['name']}` has been already declared in the code. Please give a new similar name for the variable/function `{var}` and format your response using this format: \n```json\n{{'name': '<myNewName>'}}\n```Ensure you have specified the 'name' field.\nThe new name for the variable/function `{var}` need to be more meaningful and not already used in the code.\n\nHere is the code where the variable/function `{var}` appears:\n\n```javascript\n{context}\n```"
                response = self.generate(prompt, 200)

        return name['name']