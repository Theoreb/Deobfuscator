from deobfuscator import Desobfuscator

from rich import print

engine = Desobfuscator('script.js')
engine.desobfuscate()
#print(engine.desobfuscate()[:5000])