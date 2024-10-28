import pytest # type: ignore
import esprima
import escodegen

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.visitor import *


def test_1():
    code = """
    (
  function (zonefile) {
    var rnd = Math.round(Math.random() * 999999);
    var s = document.createElement('script');
    s.type = 'text/javascript';
    s.async = true;
    var proto = document.location.protocol;
    var host = (proto == 'https:' || proto == 'file:') ? 'https://server' : '//cdn';
    if (window.location.hash == '#cpmstarDev') host = '//dev.server';
    if (window.location.hash == '#cpmstarStaging') host = '//staging.server';
    s.src = host + '.cpmstar.com/cached/zonefiles/' + zonefile + '.js?rnd=' + rnd;
    var s2 = document.getElementsByTagName('script') [0];
    s2.parentNode.insertBefore(s, s2);
    var y = window.location.href.split('#') [0].split('').reduce(function (a, b) {
      return (a << 5) - a + b.charCodeAt(0) >>> 1
    }, 0);
    y = (10 + ((y * 7) % 26)).toString(36) + y.toString(36);
    var drutObj = window[y] = window[y] ||
    {
    };
    window.cpmstarAPI = function (o) {
      (drutObj.cmd = drutObj.cmd || []).push(o);
    }
  }('98_47747_powerline')
);
    """
    ast = esprima.parseScript(code)
    print(ast)
    visitor = Visitor(ast)
    
    result = []
    visitor.set_task(lambda node, scope : (
            result.append(node.name) if node.type == Syntax.Identifier and not node.name in result else None
        ))
    visitor.visit()

    print(result)
    assert result == ['zonefile', 'rnd', 'Math', 'round', 'random', 's', 'document', 'createElement', 'type', 'async', 'proto', 'location', 'protocol', 'host', 'window', 'hash', 'src', 's2', 'getElementsByTagName', 'parentNode', 'insertBefore', 'y', 'href', 'split', 'reduce', 'a', 'b', 'charCodeAt', 'toString', 'drutObj', 'cpmstarAPI', 'o', 'cmd', 'push']

def test_2():
    code = """
    var rc = function () {
      this.loaded = !1;
      this.onLoad = null;
      this.spriteSheetLoaded = !1;
      this.gameSheet;
      this.frames = {};
      this.skullRedGlow = this.skullDarkBlueGlow = this.skullPurpleGlow = this.skullRed = this.skullDarkBlue = this.skullPurple = this.bgGrid = this.boostImage = this.keysImage = null;
      this.loadGameSpritesheet = function () {
        this.gameSheet = new Image;
        this.gameSheet.src = 'images/sheet.png?v=3';
        this.gameSheet.onload = function () {
          s.loadGameSpritesheetFrames();
          s.spriteSheetLoaded = !0;
          s.loadPatterns();
          s.skullDarkBlue = s.frames.skullbase.renderTintedFrame('#2a9de3');
          s.skullDarkBlueGlow = s.frames.skullglow.renderTintedFrame('#1931d6');
          s.skullPurple = s.frames.skullbase.renderTintedFrame('#c12ee5');
          s.skullPurpleGlow = s.frames.skullglow.renderTintedFrame('#0000FF');
          s.skullRed = s.frames.skullbase.renderTintedFrame('#ff2222');
          s.skullRedGlow = s.frames.skullglow.renderTintedFrame('#552255');
          s.loaded = !0;
          s.onLoad()
        }
      };
      this.loadPatterns = function () {
        var a = s.frames.grid.renderToCanvas();
        s.bgGrid = I.context.createPattern(a, 'repeat')
      };
      this.loadGameSpritesheetFrames = function () {
        for (var a = gameSheetInfo.length, c = 0; c < a; c++) {
          var f = gameSheetInfo[c],
          d = new hb;
          d.setFrameInfo(f, this.gameSheet);
          this.frames[f[0]] = d
        }
      };
      this.load = function (a) {
        this.onLoad = a;
        this.loadGameSpritesheet();
        this.keysImage = new Image;
        this.keysImage.src = 'images/arrows.png';
        this.keysImage.onload = function () {
        };
        this.boostImage = new Image;
        this.boostImage.src = 'images/close-to-boost-w.png';
        this.boostImage.onload = function () {
        }
      };
      this.loadTintImage = function (a, c, f) {
        var d = v.createElement('canvas'),
        k = d.getContext('2d'),
        g = a.width,
        e = a.height;
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
        c(d)
      }
    }
"""

    ast = esprima.parseScript(code)
    #print(ast)
    visitor = Visitor(ast)
    
    result = []
    visitor.set_task(lambda node, scope: (
            result.append(node.name) if node.type == Syntax.Identifier and not node.name in result else None
        ))
    visitor.visit()

    print(result)
    assert result == ['rc', 'loaded', 'onLoad', 'spriteSheetLoaded', 'gameSheet', 'frames', 'skullRedGlow', 'skullDarkBlueGlow', 'skullPurpleGlow', 'skullRed', 'skullDarkBlue', 'skullPurple', 'bgGrid', 'boostImage', 'keysImage', 'loadGameSpritesheet', 'Image', 'src', 'onload', 's', 'loadGameSpritesheetFrames', 'loadPatterns', 'skullbase', 'renderTintedFrame', 'skullglow', 'a', 'grid', 'renderToCanvas', 'I', 'context', 'createPattern', 'gameSheetInfo', 'length', 'c', 'f', 'd', 'hb', 'setFrameInfo', 'load', 'loadTintImage', 'v', 'createElement', 'k', 'getContext', 'g', 'width', 'e', 'height', 'b', 'fillStyle', 'fillRect', 'globalCompositeOperation', 'drawImage', 'globalAlpha']


def test_3():
    code = """
    ga.prototype = {
      _value: '',
      _color: '#000000',
      _stroke: !1,
      _strokeColor: '#000000',
      _strokeWidth: 3,
      _size: 16,
      _canvas: null,
      _ctx: null,
      _dirty: !1,
      _scale: 1,
      _font: 'px \"proxima-nova-1\",\"proxima-nova-2\", Arial Black',
      _usingRoundedFrame: !1,
      _hmargin: 0,
      _vmargin: - 1,
      _margin: 6,
      _frameOpacity: 0.3,
      _shadowBlur: 0,
      _roundedFrameStyle: '#006666',
      _addTop: 0,
      _minWidth: 0,
      setAddTop: function (a) {
        a != this._addTop &&
        (this._addTop = a, this._dirty = !0)
      },
      setMinWidth: function (a) {
        a != this._minWidth &&
        (this._minWidth = a, this._dirty = !0)
      },
    };
"""

    ast = esprima.parseScript(code)
    #print(ast)
    visitor = Visitor(ast)
    
    result = []
    visitor.set_task(lambda node, scope: (
            result.append(node.name) if node.type == Syntax.Identifier and not node.name in result else None
        ))
    visitor.visit()

    print(result)
    assert result == ['ga', 'prototype', '_value', '_color', '_stroke', '_strokeColor', '_strokeWidth', '_size', '_canvas', '_ctx', '_dirty', '_scale', '_font', '_usingRoundedFrame', '_hmargin', '_vmargin', '_margin', '_frameOpacity', '_shadowBlur', '_roundedFrameStyle', '_addTop', '_minWidth', 'setAddTop', 'a', 'setMinWidth']

def test_4():
    code = """
(
  function (i, s, o, g, r, a, m, t) {
    i['GoogleAnalyticsObject'] = r;
    i[r] = i[r] ||
    function () {
      (i[r].q = i[r].q || []).push(arguments)
    },
    i[r].l = 1 * new Date();
    var a = s.createElement(o),
    m = s.getElementsByTagName(o) [0];
    a.async = 1;
    a.src = g;
    m.parentNode.insertBefore(a, m)
  }
)
"""

    ast = esprima.parseScript(code)
    #print(ast)
    visitor = Visitor(ast)

def test_5():
    code = """
(
    function (i, s) {
      var m = s.getElementsByTagName(o) [0];
      a.async = 1;
      a.src = g;
      m.parentNode.insertBefore(a, m)
    }
)

class Personne {
  constructor(nom, age) {
    this.nom = nom;
    this.age = age;
  }

  direBonjour() {
    console.log(`Bonjour, je m'appelle ${this.nom} et j'ai ${this.age} ans.`);
  }

  avoirAnniversaire() {
    this.age++;
    console.log(`Joyeux anniversaire ! J'ai maintenant ${this.age} ans.`);
  }
}
    """


    ast = esprima.parseScript(code)
    print(ast)
    visitor = Visitor(ast)
    print(visitor.global_scope.children[1].children[2])
    assert visitor.global_scope.children[1].children[2].declared == set()

def test_6():
    code = """
    function testShadowFunctions(a) {
      let x = 10;
      a = 2;
      let y;
      {
        let x = 20; // Shadow function 1
        console.log(x); // 20
        let y = x;
      }
    
      {
        let x = 30; // Shadow function 2
        console.log(x); // 30
      }
    
      {
        let x = 40; // Shadow function 3
        console.log(x); // 40
      }
    
      console.log(x); // 10
    }
    """

    ast = esprima.parseScript(code)
    #print(ast)
    visitor = Visitor(ast)

    scope = visitor.global_scope.children[0]
    print(visitor.global_scope)
    scope.change_name(visitor, 'x', 'nomme')
    scope.change_name(visitor, 'y', 'Y')
    scope.change_name(visitor, 'a', 'A')
    print(scope)
    assert escodegen.generate(visitor.ast) == """function testShadowFunctions(A) {
    let nomme = 10;
    A = 2;
    let Y;
    {
        let x = 20;
        console.log(x);
        let y = x;
    }
    {
        let x = 30;
        console.log(x);
    }
    {
        let x = 40;
        console.log(x);
    }
    console.log(nomme);
}"""
def test_7():
    code = """(
  function (f, b) {
    if (!b.__SV) {
      var e;
      init.init = function (event, b, config) {
        b(config);
      };
    }
  }
)"""

    ast = esprima.parseScript(code)
    #print(ast)
    visitor = Visitor(ast)

    scope = visitor.global_scope.children[0]
    scope.change_name(visitor, 'b', 'nomme')
    print(scope)
    assert escodegen.generate(visitor.ast) == """(function (f, nomme) {
    if (!nomme.__SV) {
        var e;
        init.init = function (event, b, config) {
            b(config);
        };
    }
});"""