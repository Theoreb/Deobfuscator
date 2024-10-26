# Deobfuscator
A python deobfuscator that use various librairies to rename variables and function in javascript code using local fast LLM (provided by ollama)

It provides the LLM with some context about the code and perform the modifications on the code, with auto-saving enable.
According to my tests, llama3.2:1b seems the best model choice here.

The code itself is pure spaghetti and was coded in some hours so feel free to modify it !

Eg:

[SEARCH 'f']: Searching context for variable: f in Node of type: FunctionExpression
[CONTEXT 'f']: Found context (len: 449 chars)
function (a, c, f) {
    var d = v.createElement('canvas'), k = d.getContext('2d'), g = a.width, e = a.height;
    d.width = g;
    d.height = e;
    var b = v.createElement('canvas');
    b.width = g;
    b.height = e;
    g = b.getContext('2d');
    g.fillStyle = f;
    g.fillRect(0, 0, b.width, b.height);
    g.globalCompositeOperation = 'destination-atop';
    g.drawImage(a, 0, 0);
    k.globalAlpha = 1;
    k.drawImage(b, 0, 0);
    c(d);
}
[MODEL 'f']
[Description]: The purpose of the variable `f` in this JavaScript code is to set the fill style of a `canvas` element.

Based on its usage, I'm going to guess that the original name of `f` was "color". 

Here's how it behaves:

- It sets the fill style of `b` (the first canvas) by calling `g.fillStyle = f;`. This means it will use the color specified by `f` when drawing on the canvas.
- Then, it clears the entire canvas with a global alpha value of 1 (`k.globalAlpha = 1;`) using `g.globalCompositeOperation = 'destination-atop';`.
- Next, it draws an image onto `d` (the second canvas) at position (0, 0) by calling `g.drawImage(a, 0, 0);`. This is where the color from `f` is actually applied.
- Finally, it calls a function `c(d)` which seems to be responsible for applying any additional effects or transformations to the image.

Keep in mind that this might not be the original name of `f`, but rather an attempt to guess its intended purpose based on its usage in the code.
[MODEL]: 'f' Renamed to 'color' ('color`')
[Progress]: 18 / 1129 (1.59%)
