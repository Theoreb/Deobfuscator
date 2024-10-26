import ollama

from visitor import IdentifierType

def remove_non_alphabetic_chars(s):
    return ''.join([c for c in s if c.isalpha() or c.isdigit() or c == '_'])

class Model:
    NOT_ALLOWED = [
        'function', 'while', 'for', 'if', 'else', 
        'var', 'let', 'const', 'import', 'export',
        'true', 'false', 'null', 'undefined', 'default'
    ]
    def __init__(self, model: str = 'llama3.2:1b'):
        self.model: str = model
        self.messages: list = []
        self.already: bool = False

    def clear(self):
        self.already = False
        self.messages = [
            {
            'role': 'system',
            'content': 'You are a helpful assistant, capable of deobfuscating javascript code.',
        }
        ]
    
    def add(self, message: str):
        self.messages.append({
            'role': 'user',
            'content': message
        })

    def generate(self, variable: str, context: str, var_type: IdentifierType) -> str:
        if not self.already:
            self.add(f"Explain what is the purpose of the {var_type.value} `{variable}` in this javascript code and try to guess its original name before obfuscation. WARNING: The {var_type.value} actual name can be absolutely random (for instance, the name `f` doesn't mean function).\nIf the {var_type.value}'s purpose is unclear, provide a name that describes its function or behavior.\nHowever, some names in the obfuscated code weren't changed to ensure that the code is valid. If the {var_type.value} is a default global {var_type.value}, in javascript standard library or a third party library, don't provide others names because I want to keep it as it is. \n\nCode where the {var_type.value} `{variable}` is used: \n{context}")

        description = ollama.chat(self.model, self.messages, options={'num_predict': 512})['message']['content']

        self.messages.append({
            'role': 'assistant',
            'content': description
        })

        if not self.already:
            if len(self.messages) == 3:
                self.messages.append({
                    'role': 'user',
                    'content': f"Based on your explanation, suggest a one-word name for the {var_type.value} `{variable}`. Provide the response in this format: `The original name of the {var_type.value} `{variable}` before obfuscation is: <one-word>`."
                })
        self.messages.append({
            'role': 'assistant',
            'content': f'The original name of the {var_type.value} `{variable}` before obfuscation is: `'
        })

        response = ollama.chat(self.model, self.messages, options={'num_predict': 7})['message']['content']
        renamed = remove_non_alphabetic_chars(response.split()[0])
        if renamed in self.NOT_ALLOWED:
            print(f"The model returned a name that is not allowed. Retrying...")
            self.not_allowed(variable, var_type)
            return self.generate(variable, context, var_type)
        
        while len(renamed) < 5:
            print(f"Failed to generate a good name for the {var_type.value} `{variable}` ({renamed}) Retrying...")
            self.messages[-1]['content'] = f'The original name of the {var_type.value} `{variable}` before obfuscation is: `' + renamed
            self.messages.append({
                'role': 'user',
                'content': f"The name `{renamed}` is too short. Please suggest a name with at least 5 characters that accurately describes the {var_type.value} `{variable}`."
            })
            self.messages.append({
                'role': 'assistant',
                'content': f'Sorry, the name `{renamed}` is too short for the {var_type.value} `{variable}`. A better original name of the {var_type.value} `{variable}` before obfuscation is: `'
            })
            response = ollama.chat(self.model, self.messages, options={'num_predict': 10})['message']['content']
            renamed = remove_non_alphabetic_chars(response.split()[0])

        return description, renamed, response
    
    def not_allowed(self, var: str, var_type: IdentifierType):
        self.already = True
        self.add(f"You wanted to rename the obfuscated {var_type.value} `{var}` to a name that is not allowed because it is a default javascript keyword. Please provide a different name.")
    
    def add_already(self, var: str, renamed: str):
        self.already = True
        self.add(f"You wanted to rename the obfuscated variable `{var}` to `{renamed}` but it already exists in the code. Do you want to change it to a different name ? If not, please keep it as `_{renamed}` with an underscore at the beginning of the name ?")