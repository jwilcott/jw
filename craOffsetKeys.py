import random
from pathlib import Path
from contextlib import contextmanager
from functools import partial

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

_UI = {}
_SLIDING = False
WIN = 'craOffsetKeysWin'
_STAGGER_STYLE = 'linear'
_ICONS = {'craToggle8Icon.xpm': ['/* XPM */', 'static char *craToggle8Icon_xpm[] = {', '/* width height num_colors chars_per_pixel */', '"    29    20      256            2",', '/* colors */', '"`` c #444444",', '"`. c #4e4e4e",', '"`# c #5c5c5c",', '"`a c #606060",', '"`b c #575757",', '"`c c #636363",', '"`d c #545454",', '"`e c #646a5f",', '"`f c #6b7364",', '"`g c #6a7263",', '"`h c #63695e",', '"`i c #5f5f5f",', '"`j c #9ca197",', '"`k c #adb5a6",', '"`l c #acb7a0",', '"`m c #abb7a1",', '"`n c #aeb4aa",', '"`o c #979c94",', '"`p c #666e61",', '"`q c #636462",', '"`r c #64685f",', '"`s c #7e8577",', '"`t c #acb5a6",', '"`u c #a6bd8f",', '"`v c #a2c084",', '"`w c #89af66",', '"`x c #8ab067",', '"`y c #a3bf87",', '"`z c #a8ba97",', '"`A c #b0b2ae",', '"`B c #6f7869",', '"`C c #6d7465",', '"`D c #a3a6a0",', '"`E c #b1b1b1",', '"`F c #959a91",', '"`G c #666e60",', '"`H c #808779",', '"`I c #abb6a4",', '"`J c #a4c086",', '"`K c #6e9d42",', '"`L c #427e0a",', '"`M c #448206",', '"`N c #427e0b",', '"`O c #77a34b",', '"`P c #a6bc90",', '"`Q c #61675e",', '"`R c #6d7566",', '"`S c #6c7364",', '"`T c #afb3ad",', '"`U c #a4be8b",', '"`V c #5c902c",', '"`W c #438106",', '"`X c #1d3703",', '"`Y c #234203",', '"`Z c #7aa450",', '"`0 c #a7b999",', '"`1 c #9da19a",', '"`2 c #626461",', '"`3 c #8e9488",', '"`4 c #62675e",', '"`5 c #646b5f",', '"`6 c #a4a6a0",', '"`7 c #697062",', '"`8 c #62665e",', '".` c #aab7a0",', '".. c #669736",', '".# c #244107",', '".a c #000000",', '".b c #2e5804",', '".c c #437f08",', '".d c #a4bf89",', '".e c #afb3ac",', '".f c #5f645d",', '".g c #676d61",', '".h c #b0b0b0",', '".i c #636461",', '".j c #a8aaa6",', '".k c #8aa373",', '".l c #2b5304",', '".m c #292929",', '".n c #ffffff",', '".o c #254603",', '".p c #92b56f",', '".q c #656c61",', '".r c #686e61",', '".s c #989c94",', '".t c #b1b1af",', '".u c #50732e",', '".v c #182d02",', '".w c #162a02",', '".x c #90b36d",', '".y c #adb5a5",', '".z c #626560",', '".A c #878e81",', '".B c #61665e",', '".C c #979b92",', '".D c #5e625d",', '".E c #54723e",', '".F c #69993b",', '".G c #407b06",', '".H c #0b1401",', '".I c #3b7005",', '".J c #427f08",', '".K c #a4bf88",', '".L c #afb3ab",', '".M c #727a6a",', '".N c #626860",', '".O c #558a22",', '".P c #3e7706",', '".Q c #1b3502",', '".R c #1f3c03",', '".S c #729f47",', '".T c #a6ba96",', '".U c #a2a59f",', '".V c #707869",', '".W c #adaeac",', '".X c #9ca099",', '".Y c #60665e",', '".Z c #616261",', '".0 c #848b7f",', '".1 c #aab7a2",', '".2 c #a3c084",', '".3 c #68983b",', '".4 c #417e07",', '".5 c #417e08",', '".6 c #719f44",', '".7 c #a5be8d",', '".8 c #63695f",', '"#` c #676d60",', '"#. c #7d8479",', '"## c #aab6a2",', '"#a c #a5be8b",', '"#b c #a2c182",', '"#c c #7da657",', '"#d c #7ea758",', '"#e c #a6bb93",', '"#f c #aeb3ab",', '"#g c #72796d",', '"#h c #6a7265",', '"#i c #a4aa9f",', '"#j c #aab89c",', '"#k c #aab89d",', '"#l c #a1a49e",', '"#m c #697163",', '"#n c #666c60",', '"#o c #6e7668",', '"#p c #6e7667",', '"#q c #626361",', '"#r c #000000",', '"#s c #000000",', '"#t c #000000",', '"#u c #000000",', '"#v c #000000",', '"#w c #000000",', '"#x c #000000",', '"#y c #000000",', '"#z c #000000",', '"#A c #000000",', '"#B c #000000",', '"#C c #000000",', '"#D c #000000",', '"#E c #000000",', '"#F c #000000",', '"#G c #000000",', '"#H c #000000",', '"#I c #000000",', '"#J c #000000",', '"#K c #000000",', '"#L c #000000",', '"#M c #000000",', '"#N c #000000",', '"#O c #000000",', '"#P c #000000",', '"#Q c #000000",', '"#R c #000000",', '"#S c #000000",', '"#T c #000000",', '"#U c #000000",', '"#V c #000000",', '"#W c #000000",', '"#X c #000000",', '"#Y c #000000",', '"#Z c #000000",', '"#0 c #000000",', '"#1 c #000000",', '"#2 c #000000",', '"#3 c #000000",', '"#4 c #000000",', '"#5 c #000000",', '"#6 c #000000",', '"#7 c #000000",', '"#8 c #000000",', '"a` c #000000",', '"a. c #000000",', '"a# c #000000",', '"aa c #000000",', '"ab c #000000",', '"ac c #000000",', '"ad c #000000",', '"ae c #000000",', '"af c #000000",', '"ag c #000000",', '"ah c #000000",', '"ai c #000000",', '"aj c #000000",', '"ak c #000000",', '"al c #000000",', '"am c #000000",', '"an c #000000",', '"ao c #000000",', '"ap c #000000",', '"aq c #000000",', '"ar c #000000",', '"as c #000000",', '"at c #000000",', '"au c #000000",', '"av c #000000",', '"aw c #000000",', '"ax c #000000",', '"ay c #000000",', '"az c #000000",', '"aA c #000000",', '"aB c #000000",', '"aC c #000000",', '"aD c #000000",', '"aE c #000000",', '"aF c #000000",', '"aG c #000000",', '"aH c #000000",', '"aI c #000000",', '"aJ c #000000",', '"aK c #000000",', '"aL c #000000",', '"aM c #000000",', '"aN c #000000",', '"aO c #000000",', '"aP c #000000",', '"aQ c #000000",', '"aR c #000000",', '"aS c #000000",', '"aT c #000000",', '"aU c #000000",', '"aV c #000000",', '"aW c #000000",', '"aX c #000000",', '"aY c #000000",', '"aZ c #000000",', '"a0 c #000000",', '"a1 c #000000",', '"a2 c #000000",', '"a3 c #000000",', '"a4 c #000000",', '"a5 c #000000",', '"a6 c #000000",', '"a7 c #000000",', '"a8 c #000000",', '/* pixels */', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`a`a`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`e`f`g`h`c`c`c`c`c`c`c`c",', '"`c`c`i`c`c`c`c`c`c`c`c`c`c`c`c`f`j`k`l`m`n`o`p`c`c`c`c`c`c",', '"`c`c`a`c`c`c`q`e`r`c`c`c`c`c`s`t`u`v`w`x`y`z`A`B`c`c`a`c`c",', '"`c`c`a`c`c`C`D`E`E`F`G`c`c`H`I`J`K`L`M`M`N`O`P`A`Q`c`a`c`c",', '"`c`c`a`c`R`E`E`E`E`E`E`c`S`T`U`V`M`W`X`Y`M`M`Z`0`1`c`a`c`c",', '"`c`c`a`2`E`E`3`4`5`6`7`8`E.`..`M`M.#``.a.b`M.c.d.e.f`a`c`c",', '"`c`c`a.g`E.h.i`c`c`c.i.j`E.k`M`M.l.m.n.a.a.o`M.p`k.q`c`c`c",', '"`c`c`a.r`E.h`c`c`c`c.s`E.t.u`M`M.v.a.a.a.a.w`M.x.y.q`c`c`c",', '"`c`c`c.z`E`E.A.B`h.C`E`E.D.E.F`M.G.a.a.a.H.I.J.K.L.f`c`c`c",', '"`c`c`c`c.M`E`E`E`E`E`E.N`c.L.d.O`M.P.Q.R`M`M.S.T.U`c`c`c`c",', '"`c`c`c`c`c.V.W`E`E.X.Y`c.Z.0.1.2.3.4`M`M.5.6.7`T.8`c`c`c`c",', '"`c`c`c`c`c`c.z.r#``c`c`c`c`c#.###a#b#c#d.2#e#f#g`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c#h#i`m#j#k`k#l#m`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`2#n#o#p`5#q`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c",', '"`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c`c"'], 'craLinearKeysIcon.xpm': ['/* XPM */', 'static const char *const keys_0000_linear_xpm[]={', '/* width height ncolors chars_per_pixel */', '"24 24 256 2",', '/* colors */', '"   c #444444",', '" . c #3a3a3a",', '" X c #bdbdbd",', '" o c #3f3f3f",', '" O c #ce6940",', '" + c #5a443b",', '" @ c #62473c",', '" # c #68483c",', '" $ c #60463b",', '" % c #59433b",', '" & c #54423b",', '" * c #bdb8b6",', '" = c #774d3c",', '" - c #bbbaba",', '" ; c #69493d",', '" : c #7b4e3d",', '" > c #d06940",', '" , c #bcbcbc",', '" < c #59443b",', '" 1 c #d16a40",', '" 2 c #47413f",', '" 3 c #cf6940",', '" 4 c #4d403b",', '" 5 c #c2653f",', '" 6 c #704b3c",', '" 7 c #6c4a3d",', '" 8 c #67483c",', '" 9 c #57433b",', '" 0 c #50423a",', '" q c #434242",', '" w c #61463c",', '" e c #463e3a",', '" r c #000000",', '" t c #000000",', '" y c #000000",', '" u c #000000",', '" i c #000000",', '" p c #000000",', '" a c #000000",', '" s c #000000",', '" d c #000000",', '" f c #000000",', '" g c #000000",', '" h c #000000",', '" j c #000000",', '" k c #000000",', '" l c #000000",', '" z c #000000",', '" x c #000000",', '" c c #000000",', '" v c #000000",', '" b c #000000",', '" n c #000000",', '" m c #000000",', '" M c #000000",', '" N c #000000",', '" B c #000000",', '" V c #000000",', '" C c #000000",', '" Z c #000000",', '" A c #000000",', '" S c #000000",', '" D c #000000",', '" F c #000000",', '" G c #000000",', '" H c #000000",', '" J c #000000",', '" K c #000000",', '" L c #000000",', '" P c #000000",', '" I c #000000",', '" U c #000000",', '" Y c #000000",', '" T c #000000",', '" R c #000000",', '" E c #000000",', '" W c #000000",', '" Q c #000000",', '" ! c #000000",', '" ~ c #000000",', '" ^ c #000000",', '" / c #000000",', '" ( c #000000",', '" ) c #000000",', '" _ c #000000",', '" ` c #000000",', '" \' c #000000",', '" ] c #000000",', '" [ c #000000",', '" { c #000000",', '" } c #000000",', '" | c #000000",', '".  c #000000",', '".. c #000000",', '".X c #000000",', '".o c #000000",', '".O c #000000",', '".+ c #000000",', '".@ c #000000",', '".# c #000000",', '".$ c #000000",', '".% c #000000",', '".& c #000000",', '".* c #000000",', '".= c #000000",', '".- c #000000",', '".; c #000000",', '".: c #000000",', '".> c #000000",', '"., c #000000",', '".< c #000000",', '".1 c #000000",', '".2 c #000000",', '".3 c #000000",', '".4 c #000000",', '".5 c #000000",', '".6 c #000000",', '".7 c #000000",', '".8 c #000000",', '".9 c #000000",', '".0 c #000000",', '".q c #000000",', '".w c #000000",', '".e c #000000",', '".r c #000000",', '".t c #000000",', '".y c #000000",', '".u c #000000",', '".i c #000000",', '".p c #000000",', '".a c #000000",', '".s c #000000",', '".d c #000000",', '".f c #000000",', '".g c #000000",', '".h c #000000",', '".j c #000000",', '".k c #000000",', '".l c #000000",', '".z c #000000",', '".x c #000000",', '".c c #000000",', '".v c #000000",', '".b c #000000",', '".n c #000000",', '".m c #000000",', '".M c #000000",', '".N c #000000",', '".B c #000000",', '".V c #000000",', '".C c #000000",', '".Z c #000000",', '".A c #000000",', '".S c #000000",', '".D c #000000",', '".F c #000000",', '".G c #000000",', '".H c #000000",', '".J c #000000",', '".K c #000000",', '".L c #000000",', '".P c #000000",', '".I c #000000",', '".U c #000000",', '".Y c #000000",', '".T c #000000",', '".R c #000000",', '".E c #000000",', '".W c #000000",', '".Q c #000000",', '".! c #000000",', '".~ c #000000",', '".^ c #000000",', '"./ c #000000",', '".( c #000000",', '".) c #000000",', '"._ c #000000",', '".` c #000000",', '".\' c #000000",', '".] c #000000",', '".[ c #000000",', '".{ c #000000",', '".} c #000000",', '".| c #000000",', '"X  c #000000",', '"X. c #000000",', '"XX c #000000",', '"Xo c #000000",', '"XO c #000000",', '"X+ c #000000",', '"X@ c #000000",', '"X# c #000000",', '"X$ c #000000",', '"X% c #000000",', '"X& c #000000",', '"X* c #000000",', '"X= c #000000",', '"X- c #000000",', '"X; c #000000",', '"X: c #000000",', '"X> c #000000",', '"X, c #000000",', '"X< c #000000",', '"X1 c #000000",', '"X2 c #000000",', '"X3 c #000000",', '"X4 c #000000",', '"X5 c #000000",', '"X6 c #000000",', '"X7 c #000000",', '"X8 c #000000",', '"X9 c #000000",', '"X0 c #000000",', '"Xq c #000000",', '"Xw c #000000",', '"Xe c #000000",', '"Xr c #000000",', '"Xt c #000000",', '"Xy c #000000",', '"Xu c #000000",', '"Xi c #000000",', '"Xp c #000000",', '"Xa c #000000",', '"Xs c #000000",', '"Xd c #000000",', '"Xf c #000000",', '"Xg c #000000",', '"Xh c #000000",', '"Xj c #000000",', '"Xk c #000000",', '"Xl c #000000",', '"Xz c #000000",', '"Xx c #000000",', '"Xc c #000000",', '"Xv c #000000",', '"Xb c #000000",', '"Xn c #000000",', '"Xm c #000000",', '"XM c #000000",', '"XN c #000000",', '"XB c #000000",', '"XV c #000000",', '"XC c #000000",', '"XZ c #000000",', '"XA c #000000",', '"XS c #000000",', '"XD c #000000",', '"XF c #000000",', '"XG c #000000",', '"XH c #000000",', '"XJ c #000000",', '"XK c #000000",', '"XL c #000000",', '"XP c #000000",', '"XI c #000000",', '"XU c #000000",', '/* pixels */', '"                                                ",', '"                                                ",', '"                                                ",', '"                                 . . . . .      ",', '"                                 . X X X .      ",', '"                                 e , . X .      ",', '"                               o & - X X .      ",', '"                             o = O 9 . . .      ",', '"                           o 6 O + o            ",', '"                         o : 3 < o              ",', '"                   . . . 0 O + o                ",', '"                   . X X X . o                  ",', '"                   . X . X .                    ",', '"                 o ; * X X .                    ",', '"               o @ O 7 . . .                    ",', '"             o w 1 @ o                          ",', '"           q # 5 8 o                            ",', '"     . . . 4 > $ o                              ",', '"     . X X X % 2                                ",', '"     . X . X .                                  ",', '"     . X X X .                                  ",', '"     . . . . .                                  ",', '"                                                ",', '"                                                ",'], 'craSlopeKeysIcon.xpm': ['/* XPM */', 'static const char *const keys_0001_slope_xpm[]={', '/* width height ncolors chars_per_pixel */', '"24 24 256 2",', '/* colors */', '"   c #444444",', '" . c #bdbdbd",', '" X c #424242",', '" o c #434343",', '" O c #404040",', '" + c #414141",', '" @ c #3b3b3b",', '" # c #3a3a3a",', '" $ c #3d3d3d",', '" % c #bcbcbc",', '" & c #bbbaba",', '" * c #3c3c3c",', '" = c #3f3f3f",', '" - c #64483d",', '" ; c #45413f",', '" : c #424141",', '" > c #454545",', '" , c #494949",', '" < c #3e3e3e",', '" 1 c #646464",', '" 2 c #98776a",', '" 3 c #444342",', '" 4 c #47403d",', '" 5 c #453f3d",', '" 6 c #47413e",', '" 7 c #49413e",', '" 8 c #6a493c",', '" 9 c #473e3a",', '" 0 c #50443e",', '" q c #8d6e61",', '" w c #505050",', '" e c #9a583e",', '" r c #585858",', '" t c #6d4b3e",', '" y c #714c3d",', '" u c #ae5e3f",', '" i c #81513e",', '" p c #454241",', '" a c #83513d",', '" s c #64483c",', '" d c #7c4f3c",', '" f c #4d423d",', '" g c #58453d",', '" h c #474747",', '" j c #9c5f47",', '" k c #4d4340",', '" l c #8c543d",', '" z c #4d4d4d",', '" x c #89533e",', '" c c #b4603f",', '" v c #463f3b",', '" b c #a45b3f",', '" n c #44413f",', '" m c #484544",', '" M c #4a423e",', '" N c #57453f",', '" B c #434241",', '" V c #92563d",', '" C c #7b4f3d",', '" Z c #665954",', '" A c #5e473e",', '" S c #5a453d",', '" D c #656362",', '" F c #857b78",', '" G c #403f3f",', '" H c #8e543e",', '" J c #95563d",', '" K c #444443",', '" L c #bf6440",', '" P c #57453e",', '" I c #9d593e",', '" U c #000000",', '" Y c #000000",', '" T c #000000",', '" R c #000000",', '" E c #000000",', '" W c #000000",', '" Q c #000000",', '" ! c #000000",', '" ~ c #000000",', '" ^ c #000000",', '" / c #000000",', '" ( c #000000",', '" ) c #000000",', '" _ c #000000",', '" ` c #000000",', '" \' c #000000",', '" ] c #000000",', '" [ c #000000",', '" { c #000000",', '" } c #000000",', '" | c #000000",', '".  c #000000",', '".. c #000000",', '".X c #000000",', '".o c #000000",', '".O c #000000",', '".+ c #000000",', '".@ c #000000",', '".# c #000000",', '".$ c #000000",', '".% c #000000",', '".& c #000000",', '".* c #000000",', '".= c #000000",', '".- c #000000",', '".; c #000000",', '".: c #000000",', '".> c #000000",', '"., c #000000",', '".< c #000000",', '".1 c #000000",', '".2 c #000000",', '".3 c #000000",', '".4 c #000000",', '".5 c #000000",', '".6 c #000000",', '".7 c #000000",', '".8 c #000000",', '".9 c #000000",', '".0 c #000000",', '".q c #000000",', '".w c #000000",', '".e c #000000",', '".r c #000000",', '".t c #000000",', '".y c #000000",', '".u c #000000",', '".i c #000000",', '".p c #000000",', '".a c #000000",', '".s c #000000",', '".d c #000000",', '".f c #000000",', '".g c #000000",', '".h c #000000",', '".j c #000000",', '".k c #000000",', '".l c #000000",', '".z c #000000",', '".x c #000000",', '".c c #000000",', '".v c #000000",', '".b c #000000",', '".n c #000000",', '".m c #000000",', '".M c #000000",', '".N c #000000",', '".B c #000000",', '".V c #000000",', '".C c #000000",', '".Z c #000000",', '".A c #000000",', '".S c #000000",', '".D c #000000",', '".F c #000000",', '".G c #000000",', '".H c #000000",', '".J c #000000",', '".K c #000000",', '".L c #000000",', '".P c #000000",', '".I c #000000",', '".U c #000000",', '".Y c #000000",', '".T c #000000",', '".R c #000000",', '".E c #000000",', '".W c #000000",', '".Q c #000000",', '".! c #000000",', '".~ c #000000",', '".^ c #000000",', '"./ c #000000",', '".( c #000000",', '".) c #000000",', '"._ c #000000",', '".` c #000000",', '".\' c #000000",', '".] c #000000",', '".[ c #000000",', '".{ c #000000",', '".} c #000000",', '".| c #000000",', '"X  c #000000",', '"X. c #000000",', '"XX c #000000",', '"Xo c #000000",', '"XO c #000000",', '"X+ c #000000",', '"X@ c #000000",', '"X# c #000000",', '"X$ c #000000",', '"X% c #000000",', '"X& c #000000",', '"X* c #000000",', '"X= c #000000",', '"X- c #000000",', '"X; c #000000",', '"X: c #000000",', '"X> c #000000",', '"X, c #000000",', '"X< c #000000",', '"X1 c #000000",', '"X2 c #000000",', '"X3 c #000000",', '"X4 c #000000",', '"X5 c #000000",', '"X6 c #000000",', '"X7 c #000000",', '"X8 c #000000",', '"X9 c #000000",', '"X0 c #000000",', '"Xq c #000000",', '"Xw c #000000",', '"Xe c #000000",', '"Xr c #000000",', '"Xt c #000000",', '"Xy c #000000",', '"Xu c #000000",', '"Xi c #000000",', '"Xp c #000000",', '"Xa c #000000",', '"Xs c #000000",', '"Xd c #000000",', '"Xf c #000000",', '"Xg c #000000",', '"Xh c #000000",', '"Xj c #000000",', '"Xk c #000000",', '"Xl c #000000",', '"Xz c #000000",', '"Xx c #000000",', '"Xc c #000000",', '"Xv c #000000",', '"Xb c #000000",', '"Xn c #000000",', '"Xm c #000000",', '"XM c #000000",', '"XN c #000000",', '"XB c #000000",', '"XV c #000000",', '"XC c #000000",', '"XZ c #000000",', '"XA c #000000",', '"XS c #000000",', '"XD c #000000",', '"XF c #000000",', '"XG c #000000",', '"XH c #000000",', '"XJ c #000000",', '"XK c #000000",', '"XL c #000000",', '"XP c #000000",', '"XI c #000000",', '"XU c #000000",', '/* pixels */', '"                                                ",', '"                                                ",', '"                                     X O +      ",', '"                                 $ @ h w >      ",', '"                                 @ . . & O o    ",', '"                                 * . # % z O    ",', '"                               K 7 . . . r >    ",', '"                               3 - j Z + X $ o  ",', '"         m                     ; d e N B        ",', '"                             X S J i k          ",', '"                             n y L g +          ",', '"                       o X O P b a M X          ",', '"                       + = 1 F 2 t :            ",', '"                       X , . . & 4              ",', '"                     o + , . # % $              ",', '"                   o p 5 D . . . $              ",', '"                 X 6 s I l v * < +              ",', '"       o X   o : f C c H 0 X                    ",', '"       < . . & - V u 8 G o                      ",', '"       @ . # % q x A O                          ",', '"     X 1 . . . 9 ; X                            ",', '"     O * @ # = =                                ",', '"             o o                                ",', '"                                                ",'], 'craSteepSlopeKeysIcon.xpm': ['/* XPM */', 'static const char *const curves2_0000_SteepSlope_xpm[]={', '/* width height ncolors chars_per_pixel */', '"24 24 256 2",', '/* colors */', '"   c #444444",', '" . c #bdbdbd",', '" X c #434343",', '" o c #424242",', '" O c #414141",', '" + c #3a3a3a",', '" @ c #3d3d3d",', '" # c #404040",', '" $ c #3b3b3b",', '" % c #bcbcbc",', '" & c #bbbaba",', '" * c #3c3c3c",', '" = c #3f3f3f",', '" - c #64483d",', '" ; c #45413f",', '" : c #494949",', '" > c #646464",', '" , c #3e3e3e",', '" < c #424141",', '" 1 c #64483c",', '" 2 c #47413e",', '" 3 c #bf6440",', '" 4 c #4d4340",', '" 5 c #9d593e",', '" 6 c #6d4b3e",', '" 7 c #7b4f3d",', '" 8 c #9a583e",', '" 9 c #49413e",', '" 0 c #453f3d",', '" q c #403f3f",', '" w c #ae5e3f",', '" e c #95563d",', '" r c #714c3d",', '" t c #98776a",', '" y c #57453e",', '" u c #b4603f",', '" i c #57453f",', '" p c #44413f",', '" a c #463f3b",', '" s c #7c4f3c",', '" d c #656362",', '" f c #5f5f5f",', '" g c #434241",', '" h c #8e543e",', '" j c #444342",', '" k c #50443e",', '" l c #8c543d",', '" z c #473e3a",', '" x c #515151",', '" c c #857b78",', '" v c #a45b3f",', '" b c #444443",', '" n c #92563d",', '" m c #787878",', '" M c #4a423e",', '" N c #81513e",', '" B c #9c5f47",', '" V c #454241",', '" C c #6a493c",', '" Z c #5e5e5e",', '" A c #89533e",', '" S c #4d423d",', '" D c #58453d",', '" F c #83513d",', '" G c #47403d",', '" H c #8d6e61",', '" J c #5e473e",', '" K c #615956",', '" L c #5a453d",', '" P c #000000",', '" I c #000000",', '" U c #000000",', '" Y c #000000",', '" T c #000000",', '" R c #000000",', '" E c #000000",', '" W c #000000",', '" Q c #000000",', '" ! c #000000",', '" ~ c #000000",', '" ^ c #000000",', '" / c #000000",', '" ( c #000000",', '" ) c #000000",', '" _ c #000000",', '" ` c #000000",', '" \' c #000000",', '" ] c #000000",', '" [ c #000000",', '" { c #000000",', '" } c #000000",', '" | c #000000",', '".  c #000000",', '".. c #000000",', '".X c #000000",', '".o c #000000",', '".O c #000000",', '".+ c #000000",', '".@ c #000000",', '".# c #000000",', '".$ c #000000",', '".% c #000000",', '".& c #000000",', '".* c #000000",', '".= c #000000",', '".- c #000000",', '".; c #000000",', '".: c #000000",', '".> c #000000",', '"., c #000000",', '".< c #000000",', '".1 c #000000",', '".2 c #000000",', '".3 c #000000",', '".4 c #000000",', '".5 c #000000",', '".6 c #000000",', '".7 c #000000",', '".8 c #000000",', '".9 c #000000",', '".0 c #000000",', '".q c #000000",', '".w c #000000",', '".e c #000000",', '".r c #000000",', '".t c #000000",', '".y c #000000",', '".u c #000000",', '".i c #000000",', '".p c #000000",', '".a c #000000",', '".s c #000000",', '".d c #000000",', '".f c #000000",', '".g c #000000",', '".h c #000000",', '".j c #000000",', '".k c #000000",', '".l c #000000",', '".z c #000000",', '".x c #000000",', '".c c #000000",', '".v c #000000",', '".b c #000000",', '".n c #000000",', '".m c #000000",', '".M c #000000",', '".N c #000000",', '".B c #000000",', '".V c #000000",', '".C c #000000",', '".Z c #000000",', '".A c #000000",', '".S c #000000",', '".D c #000000",', '".F c #000000",', '".G c #000000",', '".H c #000000",', '".J c #000000",', '".K c #000000",', '".L c #000000",', '".P c #000000",', '".I c #000000",', '".U c #000000",', '".Y c #000000",', '".T c #000000",', '".R c #000000",', '".E c #000000",', '".W c #000000",', '".Q c #000000",', '".! c #000000",', '".~ c #000000",', '".^ c #000000",', '"./ c #000000",', '".( c #000000",', '".) c #000000",', '"._ c #000000",', '".` c #000000",', '".\' c #000000",', '".] c #000000",', '".[ c #000000",', '".{ c #000000",', '".} c #000000",', '".| c #000000",', '"X  c #000000",', '"X. c #000000",', '"XX c #000000",', '"Xo c #000000",', '"XO c #000000",', '"X+ c #000000",', '"X@ c #000000",', '"X# c #000000",', '"X$ c #000000",', '"X% c #000000",', '"X& c #000000",', '"X* c #000000",', '"X= c #000000",', '"X- c #000000",', '"X; c #000000",', '"X: c #000000",', '"X> c #000000",', '"X, c #000000",', '"X< c #000000",', '"X1 c #000000",', '"X2 c #000000",', '"X3 c #000000",', '"X4 c #000000",', '"X5 c #000000",', '"X6 c #000000",', '"X7 c #000000",', '"X8 c #000000",', '"X9 c #000000",', '"X0 c #000000",', '"Xq c #000000",', '"Xw c #000000",', '"Xe c #000000",', '"Xr c #000000",', '"Xt c #000000",', '"Xy c #000000",', '"Xu c #000000",', '"Xi c #000000",', '"Xp c #000000",', '"Xa c #000000",', '"Xs c #000000",', '"Xd c #000000",', '"Xf c #000000",', '"Xg c #000000",', '"Xh c #000000",', '"Xj c #000000",', '"Xk c #000000",', '"Xl c #000000",', '"Xz c #000000",', '"Xx c #000000",', '"Xc c #000000",', '"Xv c #000000",', '"Xb c #000000",', '"Xn c #000000",', '"Xm c #000000",', '"XM c #000000",', '"XN c #000000",', '"XB c #000000",', '"XV c #000000",', '"XC c #000000",', '"XZ c #000000",', '"XA c #000000",', '"XS c #000000",', '"XD c #000000",', '"XF c #000000",', '"XG c #000000",', '"XH c #000000",', '"XJ c #000000",', '"XK c #000000",', '"XL c #000000",', '"XP c #000000",', '"XI c #000000",', '"XU c #000000",', '/* pixels */', '"                                                ",', '"                                 X X            ",', '"                                 = = + $ * #    ",', '"                             o ; z . . . > o    ",', '"                           # J A H % + . $      ",', '"                       X q C w n - & . . ,      ",', '"                     o k h u 7 S < X   o X      ",', '"               O , * a l 5 1 2 o                ",', '"               @ . . . d 0 V X                  ",', '"               @ % + . : O X                    ",', '"               G & . . : o                      ",', '"             < 6 t c > = O                      ",', '"           o M F v y # o X                      ",', '"           O D 3 r p                            ",', '"           4 N e L o                            ",', '"         g i 8 s ;                              ",', '"   X @ $ O K B - j                              ",', '"     @ m . . . 9 b                              ",', '"     # f % + . *                                ",', '"     X + & . . $                                ",', '"       @ Z x + @                                ",', '"       O # o                                    ",', '"                                                ",', '"                                                ",']}


# Bundle a constant-infinity icon instead of relying on Maya's muted.png,
# which is absent in some Maya versions.
def _constant_icon():
    rows = []
    for y in range(24):
        row = ''
        for x in range(24):
            dx, dy = x - 11.5, y - 11.5
            ring = 65 <= dx * dx + dy * dy <= 100
            cross = abs(dx) <= 4.5 and abs(dy) <= 4.5 and (
                abs(dx - dy) <= 1.5 or abs(dx + dy) <= 1.5)
            row += 'r' if ring or cross else '.'
        rows.append('"' + row + '",')
    return ['/* XPM */', 'static const char *craConstantInfinity[] = {',
            '"24 24 2 1",', '". c None",', '"r c #d34b4b",'] + rows + ['};']


_ICONS['craConstantInfinity.xpm'] = _constant_icon()


@contextmanager
def _undo():
    cmds.undoInfo(openChunk=True, chunkName='craOffsetKeysUndo')
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def _pref(name, default):
    name = 'craOffsetKeys' + name + 'OV'
    return cmds.optionVar(query=name) if cmds.optionVar(exists=name) else default


def _save(name, value):
    name = 'craOffsetKeys' + name + 'OV'
    if isinstance(value, float):
        cmds.optionVar(floatValue=(name, value))
    else:
        cmds.optionVar(intValue=(name, int(value)))


def _amount(value=None, *_):
    if value is None:
        value = cmds.floatField(_UI['amount'], query=True, value=True)
    value = max(0.0, float(value))
    cmds.floatField(_UI['amount'], edit=True, value=value)
    _save('LastValue', value)
    return value


def sec_to_frames(seconds):
    return om.MTime(seconds, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())


def craOffsetKeysGetCBAttrs():
    for flag in ('selectedMainAttributes', 'selectedShapeAttributes',
                 'selectedHistoryAttributes'):
        attrs = cmds.channelBox('mainChannelBox', query=True, **{flag: True})
        if attrs:
            return attrs
    return []


def craGetAnimated(mode=1, node_type='transform'):
    objects = cmds.ls(selection=True, long=True) or []
    if not objects:
        objects = cmds.ls(type=node_type, long=True) if mode else cmds.ls(long=True)
        if mode and node_type == 'nurbsCurve':
            objects = cmds.listRelatives(objects or [], parent=True, fullPath=True) or []
    return [obj for obj in dict.fromkeys(objects or [])
            if not cmds.nodeType(obj).startswith('animCurve')
            and cmds.keyframe(obj, query=True, keyframeCount=True)]


def _time_range():
    slider = mel.eval('$tmp = $gPlayBackSlider')
    if cmds.timeControl(slider, query=True, rangeVisible=True):
        return cmds.timeControl(slider, query=True, rangeArray=True)
    return None


def craOffsetKeysProc(objects, framesOffset, mode=0, sorting=1,
                      direction=1, changeMode=' -tc ', stagger='linear'):
    """Offset keys. mode: 0 normal, 1 stagger, 2 random; sorting: 1..5.

    Selected Graph Editor keys take precedence over Channel Box attributes
    and the highlighted timeline range. The caller can group edits for undo.
    """
    objects = list(objects or [])
    curves = cmds.keyframe(query=True, selected=True, name=True) or []
    if curves:
        objects = list(dict.fromkeys(curves))
    if not objects:
        if cmds.confirmDialog(title='Nothing selected', message='Use all animated objects?',
                              button=['Yes', 'No'], cancelButton='No',
                              dismissString='No') != 'Yes':
            return
        transforms = cmds.confirmDialog(title='Offset animated', message='Transforms/Joints only?',
                                        button=['Yes', 'No'], cancelButton='No',
                                        dismissString='No') == 'Yes'
        objects = craGetAnimated(int(transforms), 'transform')
        if objects:
            cmds.select(objects, replace=True)
    if sorting == 2:
        objects.reverse()
    elif sorting in (3, 4):
        objects.sort(reverse=sorting == 4)
    elif sorting == 5:
        random.shuffle(objects)
    attrs = [] if curves else craOffsetKeysGetCBAttrs()
    time_range = _time_range()
    step = framesOffset * direction
    offset = 0.0
    is_time = changeMode.strip() in ('-tc', 'tc', 'timeChange')
    for index, obj in enumerate(objects, 1):
        if mode == 2:
            offset = random.uniform(0, step + direction)
            if is_time:
                offset = int(offset)
        elif mode == 1:
            if stagger == 'linear' or index == 1:
                offset += step
            elif stagger == 'slope':
                offset += step * index / len(objects)
            else:
                offset += step / index
        else:
            offset = step
        flags = dict(edit=True, relative=True, option='over', adjustBreakdowns=True)
        flags['timeChange' if is_time else 'valueChange'] = offset
        if attrs:
            flags['attribute'] = attrs
        if curves:
            flags['animation'] = 'keys'
        elif time_range:
            flags['time'] = tuple(time_range)
            flags['includeUpperBound'] = False
        else:
            flags['animation'] = 'objects'
        cmds.keyframe(obj, **flags)


def craOffsetKeysWrapper(direction, changeMode, *_):
    amount = _amount()
    mods = cmds.getModifiers()
    amount *= {5: 0.1, 4: 0.5, 1: 1.5, 8: 2.0}.get(mods, 1.0)
    mode = 1 if cmds.iconTextCheckBox(_UI['stagger'], query=True, value=True) else 0
    if cmds.iconTextCheckBox(_UI['random'], query=True, value=True):
        mode = 2
    with _undo():
        craOffsetKeysProc(cmds.ls(selection=True, long=True), amount, mode,
                          cmds.optionMenu(_UI['sort'], query=True, select=True),
                          direction, changeMode,
                          _STAGGER_STYLE)


def craOffsetSlider(mode, *_):
    global _SLIDING
    if not (cmds.ls(selection=True) or cmds.keyframe(query=True, selected=True, name=True)):
        return
    value = cmds.floatSlider(_UI[mode], query=True, value=True)
    if not value:
        return
    if not _SLIDING:
        cmds.undoInfo(openChunk=True, chunkName='craOffsetKeysSlider')
        _SLIDING = True
    try:
        craOffsetKeysWrapper(1 if value > 0 else -1, mode)
    except Exception:
        craStopOffsetSlider()
        raise


def craStopOffsetSlider(*_):
    global _SLIDING
    for mode in (' -tc ', ' -vc '):
        if mode in _UI and cmds.floatSlider(_UI[mode], exists=True):
            cmds.floatSlider(_UI[mode], edit=True, value=0)
    if _SLIDING:
        cmds.undoInfo(closeChunk=True)
        _SLIDING = False


def craToggleOffsetSliders(*_):
    visible = not cmds.columnLayout(_UI['sliders'], query=True, visible=True)
    cmds.columnLayout(_UI['sliders'], edit=True, visible=visible)
    _save('Sliders', visible)


def craGetCurrentChannelValue(*_):
    selection = cmds.ls(selection=True) or []
    attrs = craOffsetKeysGetCBAttrs()
    _amount(abs(cmds.getAttr(selection[0] + '.' + attrs[0])) if selection and attrs else 1)


def craSetZeroCurrentFrame(mode=0, *_):
    objects = cmds.ls(selection=True, long=True) or []
    attrs = craOffsetKeysGetCBAttrs()
    mode = mode or cmds.getModifiers()
    defaults = {1: ['tx', 'ty', 'tz'], 5: ['tx', 'tz'],
                4: ['rx', 'ry', 'rz'], 8: ['sx', 'sy', 'sz']}
    channels = attrs or defaults.get(mode, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz'])
    if not objects:
        cmds.warning('Nothing selected')
        return
    with _undo():
        for obj in objects:
            for attr in channels:
                plug = obj + '.' + attr
                if not cmds.objExists(plug):
                    continue
                target = 1.0 if mode == 8 and not attrs else 0.0
                value = cmds.getAttr(plug)
                if cmds.keyframe(plug, query=True, keyframeCount=True):
                    cmds.keyframe(plug, edit=True, relative=True, valueChange=target - value,
                                  animation='objects')
                    if not attrs:
                        cmds.setKeyframe(plug, value=target)
                elif cmds.getAttr(plug, settable=True):
                    cmds.setAttr(plug, target)


def craOffsetKeysCycle(mode, *_):
    settings = [('preInfinite', 'constant'), ('preInfinite', 'cycleRelative'),
                ('preInfinite', 'cycle'), ('postInfinite', 'cycle'),
                ('postInfinite', 'cycleRelative'), ('postInfinite', 'constant'),
                ('preInfinite', 'linear'), ('preInfinite', 'oscillate'),
                ('postInfinite', 'linear'), ('postInfinite', 'oscillate')]
    objects = cmds.ls(selection=True, long=True) or []
    if objects:
        flags = {settings[mode][0]: settings[mode][1]}
        attrs = craOffsetKeysGetCBAttrs()
        if attrs:
            flags['attribute'] = attrs
        with _undo():
            cmds.setInfinity(objects, **flags)


def _toggle_infinity(*_):
    editor = 'graphEditor1GraphEd'
    if cmds.animCurveEditor(editor, exists=True):
        visible = cmds.animCurveEditor(editor, query=True, displayInfinities=True)
        cmds.animCurveEditor(editor, edit=True, displayInfinities=not visible)


def _mode(which, value):
    other = 'random' if which == 'stagger' else 'stagger'
    _save('Stagger' if which == 'stagger' else 'Random', value)
    if value:
        cmds.iconTextCheckBox(_UI[other], edit=True, value=False)
        _save('Random' if which == 'stagger' else 'Stagger', False)
    cmds.rowLayout(_UI['slope_row'], edit=True,
                   enable=cmds.iconTextCheckBox(_UI['stagger'], query=True, value=True))


def _stagger_style(style, *_):
    global _STAGGER_STYLE
    _STAGGER_STYLE = style
    for name in ('linear', 'slope', 'steep slope'):
        cmds.iconTextCheckBox(_UI[name], edit=True, value=name == style)


def _select_animated(mode, node_type, *_):
    cmds.select(clear=True)
    objects = craGetAnimated(mode, node_type)
    if objects:
        cmds.select(objects, replace=True)


def _select_animation_curves(*_):
    """Select time-input animation curves, excluding set driven key curves."""
    curves = cmds.ls(type=['animCurveTA', 'animCurveTL', 'animCurveTT', 'animCurveTU']) or []
    if curves:
        cmds.select(curves, replace=True)
    else:
        cmds.select(clear=True)


def craOffsetKeysAboutScript(*_):
    name = 'craOffsetKeysAboutWin'
    if cmds.window(name, exists=True):
        cmds.deleteUI(name)
    cmds.window(name, title='About Offset Keyframes', widthHeight=(320, 220))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
    cmds.text(label='Offset Keyframes - Python port of v3.0.1')
    cmds.text(label='Original author: Carlos Rico Adega\ncarlos.rico.3d@gmail.com')
    cmds.text(label='Offset times and values; stagger, randomize,\ncycle, and zero animation channels.')
    for label, url in [('Gumroad', 'https://gumroad.com/cra3d'),
                       ('Downloads', 'https://www.highend3d.com/users/charliewales/free/downloads'),
                       ('LinkedIn', 'https://www.linkedin.com/in/carlos-rico-adega-3250586'),
                       ('Vimeo', 'https://vimeo.com/channels/749131'),
                       ('YouTube', 'https://www.youtube.com/channel/UCXnSX8PHpQtwJR-uN-atO3Q')]:
        cmds.button(label=label, annotation='Open the original author?s ' + label + ' page.', command=lambda _, u=url: cmds.showHelp(u, absolute=True))
    cmds.showWindow(name)


def _icon_button(label, icon, tooltip, command):
    """Use Maya's bundled icons alongside readable text labels."""
    return cmds.iconTextButton(style='iconAndTextHorizontal', image1=icon,
                               label=label, annotation=tooltip, height=28,
                               command=command)


def craOffsetKeys():
    """Open the compact, original-style Offset Keyframes window."""
    craStopOffsetSlider()
    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN)
    _UI.clear()
    icon_dir = Path(cmds.internalVar(userBitmapsDir=True))
    icon_dir.mkdir(parents=True, exist_ok=True)
    for filename, lines in _ICONS.items():
        path = icon_dir / filename
        if not path.exists():
            path.write_text('\n'.join(lines), encoding='ascii')

    width = 300
    cmds.window(WIN, title='Offset Keyframes', widthHeight=(width, 236),
                sizeable=True, minimizeButton=False, maximizeButton=True,
                closeCommand=craStopOffsetSlider)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=3, width=width)

    def frame():
        cmds.frameLayout(labelVisible=False, borderVisible=True,
                         marginWidth=2, marginHeight=2)

    def end_frame():
        cmds.setParent('..')
        cmds.setParent('..')

    def button(icon, tip, command, color=None, w=36):
        flags = dict(style='iconOnly', image1=icon, width=w, height=36,
                     annotation=tip, command=command)
        if color:
            flags['backgroundColor'] = color
        return cmds.iconTextButton(**flags)

    frame()
    cmds.rowLayout(numberOfColumns=4, columnWidth4=(174, 38, 38, 38))
    _UI['sort'] = cmds.optionMenu(width=172, height=36,
        annotation='Choose the object order for stagger and random offsets.')
    for label in ('sort: as selected', 'sort: reverse selection', 'sort: name [A-Z]',
                  'sort: name [Z-A]', 'sort: random'):
        cmds.menuItem(label=label)
    button('out_transform.png', 'Select all animation curves, excluding set driven keys.\nRight-click for more selection options.',
           _select_animation_curves)
    cmds.popupMenu()
    cmds.menuItem(label='All animation curves', command=_select_animation_curves)
    for label, mode, node_type in [('Animated transforms and joints', 1, 'transform'),
                                  ('All animated nodes', 0, ''),
                                  ('Animated curves', 1, 'nurbsCurve'),
                                  ('Animated joints', 1, 'joint')]:
        cmds.menuItem(label=label, command=partial(_select_animated, mode, node_type))
    button('getGraphEditor.png', 'Open Graph Editor.\nRight-click for panel layouts.', lambda *_: mel.eval('GraphEditor;'))
    cmds.popupMenu()
    for layout in ('Persp/Graph', 'Persp/Graph/Outliner', 'Persp/Graph/Hypergraph'):
        cmds.menuItem(label=layout, command=lambda _, l=layout: mel.eval('setNamedPanelLayout "' + l + '";'))
    button('QR_help.png', 'About this tool and the original author.', craOffsetKeysAboutScript)
    end_frame()

    frame()
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(83, 126, 83))
    stagger = bool(_pref('Stagger', 0))
    _UI['stagger'] = cmds.iconTextCheckBox(style='textOnly', label='Stagger',
        width=81, height=36, value=stagger, backgroundColor=(.2, .2, .2),
        annotation='Increment the offset for each object in sort order.\nEnabling Stagger turns Random off.',
        changeCommand=partial(_mode, 'stagger'))
    _UI['slope_row'] = cmds.rowLayout(numberOfColumns=3, enable=stagger,
                                     columnWidth3=(41, 41, 41))
    for name, image, tip in [
        ('linear', 'craLinearKeysIcon.xpm', 'Linear: add the same increment for each object.'),
        ('slope', 'craSlopeKeysIcon.xpm', 'Slope: after the first object, add amount ? index / object count.'),
        ('steep slope', 'craSteepSlopeKeysIcon.xpm', 'Steep slope: after the first object, add amount / index.')]:
        _UI[name] = cmds.iconTextCheckBox(style='iconOnly', image1=str(icon_dir / image),
            width=36, height=36, value=_STAGGER_STYLE == name, annotation=tip,
            changeCommand=partial(_stagger_style, name))
    cmds.setParent('..')
    _UI['random'] = cmds.iconTextCheckBox(style='textOnly', label='Random',
        width=81, height=36, value=bool(_pref('Random', 0)) and not stagger,
        backgroundColor=(.2, .2, .2),
        annotation='Random offset per object; time offsets use whole frames.\nEnabling Random turns Stagger off.',
        changeCommand=partial(_mode, 'random'))
    end_frame()

    frame()
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=7, columnWidth=[(1, 38), (2, 38), (3, 34), (4, 66), (5, 34), (6, 38), (7, 38)])
    hint = '\nAlt: ?2; Shift: ?1.5; Ctrl: ?0.5; Ctrl+Shift: ?0.1.\nUses selected keys, Channel Box channels, or highlighted timeline range.'
    for image, direction, tip in [('timeprev.png', -1, 'Move keys earlier.'),
                                  ('timenext.png', 1, 'Move keys later.')]:
        button(image, tip + hint, partial(craOffsetKeysWrapper, direction, ' -tc '), (.4, .2, .2))
    button('channelBox.png', 'Get the absolute value of the first selected channel, or 1.\nRight-click to toggle sliders.',
           craGetCurrentChannelValue, w=30)
    cmds.popupMenu()
    cmds.menuItem(label='Toggle sliders', command=craToggleOffsetSliders)
    _UI['amount'] = cmds.floatField(value=_pref('LastValue', 1), minValue=0,
        precision=2, width=63, height=32, changeCommand=_amount,
        annotation='Offset amount in frames or channel units; saved between sessions.\nRight-click for presets. Middle-click to use the current frame.')
    cmds.popupMenu()
    cmds.menuItem(divider=True, dividerLabel='Seconds to frames')
    for seconds in (.5, 1, 2, 3, 4, 5, 10):
        cmds.menuItem(label='{} seconds'.format(seconds), command=lambda _, s=seconds: _amount(sec_to_frames(s)))
    cmds.menuItem(divider=True, dividerLabel='Offset amount')
    for value in (1, 5, 10, 100, 1000, .1, .01, .001, .5, .05, .005):
        cmds.menuItem(label=str(value), command=lambda _, v=value: _amount(v))
    cmds.popupMenu(parent=_UI['amount'], button=2,
                   postMenuCommand=lambda *_: _amount(cmds.currentTime(query=True)))
    button('teZeroKey.png', 'Zero the current frame by offsetting channel animation.\nShift: translation; Ctrl+Shift: XZ; Ctrl: rotation; Alt: scale to 1.\nRight-click for reset options.',
           partial(craSetZeroCurrentFrame, 0), w=30)
    cmds.popupMenu()
    for label, mode in [('Translation and rotation', 0), ('Translation', 1),
                        ('Translation XZ', 5), ('Rotation', 4), ('Scale to one', 8)]:
        cmds.menuItem(label=label, command=partial(craSetZeroCurrentFrame, mode))
    for image, direction, tip in [('timeend.png', -1, 'Decrease key values.'),
                                  ('timestart.png', 1, 'Increase key values.')]:
        button(image, tip + hint, partial(craOffsetKeysWrapper, direction, ' -vc '), (.2, .2, .4))
    cmds.setParent('..')
    _UI['sliders'] = cmds.columnLayout(adjustableColumn=True, visible=bool(_pref('Sliders', 1)))
    for mode, color, label in [(' -tc ', (.4, .2, .2), 'time'),
                               (' -vc ', (.2, .2, .4), 'values')]:
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2,
                       columnWidth3=(20, 252, 20))
        cmds.text(label='-', width=20, height=25)
        _UI[mode] = cmds.floatSlider(minValue=-10, maxValue=10, value=0, step=1,
            height=25, backgroundColor=color,
            annotation='Drag left to subtract or right to add the offset amount to ' + label +
                       ' repeatedly.\nRelease to center the slider. One undo step per drag.',
            dragCommand=partial(craOffsetSlider, mode), changeCommand=craStopOffsetSlider)
        cmds.text(label='+', width=20, height=25)
        cmds.setParent('..')
    cmds.setParent('..')
    end_frame()

    frame()
    cmds.rowLayout(numberOfColumns=7, columnWidth=[(1, 40), (2, 40), (3, 40), (4, 52), (5, 40), (6, 40), (7, 40)])
    icons = [str(icon_dir / 'craConstantInfinity.xpm'), 'preInfinityCycleOffset.png', 'preInfinityCycle.png',
             'postInfinityCycle.png', 'postInfinityCycleOffset.png', str(icon_dir / 'craConstantInfinity.xpm')]
    descriptions = ['hold the first value', 'repeat with value offset', 'repeat animation',
                    'repeat animation', 'repeat with value offset', 'hold the last value']
    for mode in (0, 1, 2, None, 3, 4, 5):
        if mode is None:
            button(str(icon_dir / 'craToggle8Icon.xpm'), 'Toggle infinity display in the main Graph Editor.',
                   _toggle_infinity, w=48)
            continue
        pre = mode < 3
        button(icons[mode], ('Pre-infinity: ' if pre else 'Post-infinity: ') +
               descriptions[mode] + '.\nApplies to selected objects or channels.\nRight-click for linear and oscillate.',
               partial(craOffsetKeysCycle, mode), w=38)
        cmds.popupMenu()
        cmds.menuItem(label='Linear', command=partial(craOffsetKeysCycle, 6 if pre else 8))
        cmds.menuItem(label='Oscillate', command=partial(craOffsetKeysCycle, 7 if pre else 9))
    end_frame()
    cmds.showWindow(WIN)
    return WIN


if __name__ == '__main__':
    craOffsetKeys()
