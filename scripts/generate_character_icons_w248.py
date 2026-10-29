#!/usr/bin/env python3
"""W248 HUD masks. Offline; only Pillow is required. Writes 19 declared assets.

Class SVG path data: Destiny Item Manager (MIT, notice in output manifest).
Element alpha data: Bungie transparentIconPath; encoded losslessly below.
No Java, pack registries or files outside the declared output list are touched.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import zlib

from PIL import Image, ImageDraw
import PIL

SIZE = 64
SUPERSAMPLE = 8
SOURCE = {
    'class_hunter_w248': {
        'kind': 'dim_svg_path',
        'attribution': 'Destiny Item Manager, MIT; Destiny class insignia reference',
        'source_url': (
            'https://raw.githubusercontent.com/DestinyItemManager/DIM/60581be6c7063e7115a40e5939a791d'
            '58d3448f4/src/app/shell/icons/custom/Hunter.ts'
        ),
        'source_revision': '60581be6c7063e7115a40e5939a791d58d3448f4',
        'source_file_sha256': 'a99396243bc98fdfac88829dfd2217a2b76c3324e4ee65249b1c9091710e976d',
        'svg_path_sha256': 'b9a7a1bae3e044a252805541f3f2560daa57e2a0ab419188850641412abd7683',
        'svg_path': (
            'm9.055 10.446 6.945-.023-6.948 10.451 6.948-.024-7.412 '
            '11.15h-7.045l7.036-10.428h-7.036l7.032-10.422h-7.032l7.507-11.126 6.95-.024zm13.89 '
            '0-6.945-10.446 6.95.024 7.507 11.126h-7.032l7.032 10.422h-7.036l7.036 '
            '10.428h-7.045l-7.412-11.15 6.948.024-6.948-10.451z'
        ),
        'source_viewbox': [0, 0, 32, 32],
    },
    'class_titan_w248': {
        'kind': 'dim_svg_path',
        'attribution': 'Destiny Item Manager, MIT; Destiny class insignia reference',
        'source_url': (
            'https://raw.githubusercontent.com/DestinyItemManager/DIM/60581be6c7063e7115a40e5939a791d'
            '58d3448f4/src/app/shell/icons/custom/Titan.ts'
        ),
        'source_revision': '60581be6c7063e7115a40e5939a791d58d3448f4',
        'source_file_sha256': '0de62f3d89f4a6c1e183865f680a821c48d494c055f638636c58039f255da241',
        'svg_path_sha256': '624c821cbef74601f28b82a7e9542816658c528fa720311a86a0ebc70f2d2361',
        'svg_path': (
            'm14.839 15.979-13.178-7.609v15.218zm2.322 0 13.178 '
            '7.609v-15.218zm5.485-12.175-6.589-3.804-13.178 7.609 13.178 7.609 13.179-7.609zm0 '
            '16.784-6.589-3.805-13.178 7.609 13.178 7.608 13.179-7.608-6.59-3.805z'
        ),
        'source_viewbox': [0, 0, 32, 32],
    },
    'class_warlock_w248': {
        'kind': 'dim_svg_path',
        'attribution': 'Destiny Item Manager, MIT; Destiny class insignia reference',
        'source_url': (
            'https://raw.githubusercontent.com/DestinyItemManager/DIM/60581be6c7063e7115a40e5939a791d'
            '58d3448f4/src/app/shell/icons/custom/Warlock.ts'
        ),
        'source_revision': '60581be6c7063e7115a40e5939a791d58d3448f4',
        'source_file_sha256': 'b8dadaad5c0a3ff0eaca8f79a8ec74df44a065ca925bda5ed47edf1c2a7a0b74',
        'svg_path_sha256': '1e65f7fd02bc1dbb50a7a2339c23897a4ada65ab0e21fb6664a7e3fe690ff26e',
        'svg_path': (
            'm5.442 23.986 7.255-11.65-2.71-4.322-9.987 15.972zm5.986 0 4.28-6.849-2.717-4.333-6.992 '
            '11.182zm7.83-11.611 7.316 11.611h5.426l-10.015-15.972zm-7.26 '
            '11.611h8.004l-4.008-6.392zm6.991-11.182-2.703 4.324 4.302 6.858h5.413zm-5.707-.459 '
            '2.71-4.331 2.71 4.331-2.703 4.326z'
        ),
        'source_viewbox': [0, 0, 32, 32],
    },
    'subclass_arc_w248': {
        'kind': 'bungie_official_alpha',
        'attribution': 'Bungie, Destiny 2 damage-type transparent icon',
        'source_url': 'https://www.bungie.net/img/destiny_content/damage_types/destiny2/arc_trans.png',
        'definition_hash': 2303181850,
        'definition_table': 'DestinyDamageTypeDefinition',
        'definition_file_sha256': '907a7f844adb9b0e1c36395b5ea3604ef07b3ab1d04a14c845189dffa86ba750',
        'source_png_sha256': 'c8a052a2906a50461b64b352d2d92d101a2874268f40eee6c2283f3b902f5ec6',
        'source_size': [96, 96],
        'source_alpha_sha256': 'a139ecdd6da46913cb0917d218e94cdcea2664c48ad670884a1df9d852835a86',
        'source_rgb': [255, 255, 255],
        'alpha_encoding': '96x96 row-major 8-bit alpha, zlib+base85',
        'alpha_zlib_b85': (
            'c-rlmUr3Z$6u|E|YRo`crWR}qxwW#{HqK&8U}6!juodBEFRrpa6zzf=wBb`uKD2DRVBo^~WFiIXE}{JqqOgoW+BG'
            'tEabTkuN^@Et3~^LO7@avgqmFaG`<?smW9A|7yv>|*f9L)^_k8CPvL<Wte#oWV)bei)Z&0wZJFN1%;X$U<XwyBnR'
            'emeLb-TpoQy*C7{|EqWHlayb0Ob6PExX)B$p2@fe7G!XxpyXNQOH&2S2kXK<eQCQnh<qOOaT`JbN?o0upL((yyl0'
            'vMCvh%1Ix-YT>cf{@?G~KA)#ut`Sulc9S2_+;qkY&hbesU2;M$Dw5$&w$Mqe6^BtZ!iVm}fc;g?5kFNsL<^)l`t#'
            '+KILtvlafW=2xhG;JX#xH$ppu=Ple}8;0>cofh2*04$NC*FJ!S>#ru$$V$D%-)t&ud*^@S{70C(lcbv%skOWRc}N'
            'JTnX(eA~n)`vg5wV^<OrvCL09`Ie=FH%}5dY=7}O^Env#UwXlem){@zY5SLy{XpXH=n57OnCb8&OCg5#7&??4|N9'
            'H--#S+}LWdz0JlPS#x|H@e$mF3@?Gk9g##}4K4=Ccv=4rEo%uyM>FH`vzYcRGPjCSl?67gi+Yj$EczDpvWkZN}2e'
            'wE<6>^gX2dj?vfi6^8ywRl4MQ;R3=h%$aS-Abm_sowv``z`SELmD&G`?0=*7M&Gd_)R;p&zaWRLxJ<UNqZv>3jM;'
            'Fx&Kb-Ewpn2#UCTbcuVvAD=i1#;&{S$0FO&G_~~OfUgQA!O4J?nu#Lm<38)J5S9+*|gRA<-DB~u4P2xi#EIJO^c+'
            '|Wh-hvcf;((LGt$(hJmpJg_UpV>xB=O<j^{9iLqe+>c*c#wpq1nA^4$Sy*W_NJDfJnuVz(M7T(Qy;LM}6Cu+~zvq'
            'pRX~U;8QXvbbub;@3dmiQ7_*C9vvo}S`N~_8Pkl<jhgX4^M`j@H_UX7?iIH2=Xo6mE&7-6whr|?1w#22@`ycm)E#'
            'tMNrdc!%KV6hx|Y35V+HzCiw7uAEgqiPl8gW8A@j%AS|{wL1V7<)G7es^)4=!1rsH%p3uCrdLlW^XVlg@Ei7`rSR'
            '!t8Fq^nuAWXL#Bj1ug`V%3b5&0=&A+M$BaLT}06U3Jv21FIkWUfr9L8S_ekq1aGAyPGi2eM#HNKbLYxkkZj%x&Rx'
            'M&*(Voqb&cF9kM+0<@olbof!Fl7!xNtGdm#(`aYIE<8d+tWLRWU%z{a3s6xCchg)pTGZm<z&2&*rC0Z1UDxho*+F'
            'O7Wz~?_OHQX0iZBoz27fl-JPfO7Pdo%X35sWwL=HjVNEG3n-Hne~rM016Tc;+&~!ylTZ>2n?j=YgODZyrxeL!4ys'
            'NRYlw+qd!_AR@d4tOMXbaFA*`GrRBNKX6>(&hHr}bkI_t$aVbJ4if$Y%9~C6{oz?^UxR3xmR>e|kFGXWe#9@U#7^'
            '5@(eY`HVa{SZ)4gj;hP3Vk5GWJZ?%JaKi&h`_-0;dJOA4+7v|8r(XUi|v2Z9485r;}GZ^Q7d)IKBUULtF<Chv#*4'
            '=C(3N&'
        ),
    },
    'subclass_solar_w248': {
        'kind': 'bungie_official_alpha',
        'attribution': 'Bungie, Destiny 2 damage-type transparent icon',
        'source_url': 'https://www.bungie.net/img/destiny_content/damage_types/destiny2/thermal_trans.png',
        'definition_hash': 1847026933,
        'definition_table': 'DestinyDamageTypeDefinition',
        'definition_file_sha256': '907a7f844adb9b0e1c36395b5ea3604ef07b3ab1d04a14c845189dffa86ba750',
        'source_png_sha256': '255e58edaa8cdfa9a52d9cfc0a36424dd3fc77541ec25e646e8ff07e288c6168',
        'source_size': [96, 96],
        'source_alpha_sha256': '159f6136aab6a805eade825d8ae026ad5cf48b74a73e42e4880f7a42f82628cc',
        'source_rgb': [255, 255, 255],
        'alpha_encoding': '96x96 row-major 8-bit alpha, zlib+base85',
        'alpha_zlib_b85': (
            'c-rlmJxmlq6o5~|o#1(>IY{_vP{E4=(E=g`6dZyv(MThOg^Gp2Lb;Hj#0nvV7zGMQ2xtKfKb3_R#vB2q(S(Q?FbE'
            'MFPzVTwT)>0Faas0u-rL*5nZ4P<<X*+R_vT}7cIN%eS}akCN>mu-fVuee)pRrQ`@F=v&qV%pLdbRV@XkevzvwiL-'
            '$iz$%Pf2$*_A?b@Uc@0e=61#ejN!)of-I3ewFV(Wy02fOQ^gRe+X_7C^tpp6P6HvDZ!MjPet${C?;Ad7KuOfJ%s='
            'LkU)Mb36)lH_<}z={67W40|OReVd4qVmnUNIIoo0Q+c`oq`Zx(E<07(s0|_q;0#+xm2S1P_cy)eX`Ym>aG^_K_@='
            ')jsX;$a6)nffDaD{Amb+&UQT`u0P<JJiHwRka_Wo0u~)*8oWZ{d(>m$h~rOt-R);$ueelU`8t7qEIH#vuPb=5(uu'
            'Zfv-34DZ5QeV*2x&Ut(&Tt@Kwhw)RE0$V9I4evL=zl#}t$k>OCclq%tYlyIzh^&c=$hwxy&F{xgcvWM*ip~AJ_!2'
            'z-MTo-->`=nF^}nLozmh^cl71nNuY8B#Hu-0{c@w+b=E2APKy%;dI=w+YKjJv}HE62u7_}Use;)H8uNscW$Ggu%E'
            'l0l`r2`M%!R$Yv0!@4mPG=iw11J1F@~dFxe}dEeS=4YQKmupzFv|}eKe6I-(PKRVJ<>aA{0{U+kC10BBfkk%nV>?'
            'rCTp&N>H<}!O^ke$pUzXgV@}r0IjHJ9%5QA=6L3xsFg#XtkAbcSIv;1^mxl?Au1!U`3GzuY4726j%?eC?uT|~qFi'
            'DiHr5OTI%SP3g0q8O)kw7FIV&c!x2^Rrp8t|vV|Gh}nGfeyq)qfCZAA~I#2373_6Q5GtAl&10xdsw~o2vQv6F}Li'
            'sr);EZNeZQMBGemmk~Iv7tNXYYViaD+pCb)<rN5XY6-@~{}2r5R8^$Y8x>J=FkO6L;y+isy;L=<!yl$*ucCU!mD}'
            'knJgeK>oeg>UY&kwn@oxM_i%MIsMn#jx7C=908<Qbj{*boK`N$amE49}PKXv&(Rr}LjMI|FYepPnwRTZnc{8iQ7y'
            'E~3&O~Cb<pZiUh|4p-?_3YPS3v%OT4~}2z@?QqccDW5);J7d=lL1$P!#lcswcfcR56gH8&^}buC-`*mz68`N^l{b'
            'Cj-A3|GgZIN(bPq$J9&A^!Pz`6!+dHR4Z)AvV7^}FZXxs5r8k_Z*2)VS{DN9jXGw2&J&(V^b4!apqF!EP&m#P+dM'
            'RL)ntY$zNCSLs3052_0{}me0;`#&bH*C@j7dW7(c-pjOrejJ(GvF_A(I(KFE|cM+w>0ngi+Db)lvaJUPvdS_izLk'
            'KsQ!M^&aMGvT`G`3o>VWp!;AL+rjQYd*mP6TpeTix`zC*4wprQBzme&hA2-~c@o9l(A%`_d5p~xm8ksx@)w-yzi9'
        ),
    },
    'subclass_void_w248': {
        'kind': 'bungie_official_alpha',
        'attribution': 'Bungie, Destiny 2 damage-type transparent icon',
        'source_url': 'https://www.bungie.net/img/destiny_content/damage_types/destiny2/void_trans.png',
        'definition_hash': 3454344768,
        'definition_table': 'DestinyDamageTypeDefinition',
        'definition_file_sha256': '907a7f844adb9b0e1c36395b5ea3604ef07b3ab1d04a14c845189dffa86ba750',
        'source_png_sha256': '5cfb66b1499008f2ebd0396e759df7be2c38e068a76b7d52499eb482c908d151',
        'source_size': [96, 96],
        'source_alpha_sha256': '7ee2f624fa40c79a484934436e05f3157f63443be7099934f3bccc224481543c',
        'source_rgb': [255, 255, 255],
        'alpha_encoding': '96x96 row-major 8-bit alpha, zlib+base85',
        'alpha_zlib_b85': (
            'c-rk*YfMx}6rP2J@+iS-B@vY(wGpKW0!6S`ip12WvPuJ{grqT+gbe}GO(Oy^7Sd9yMev6SX#62DP^cC{F;!@7p$L'
            '|j6{RgfZHrb!USe@wVR_u%J9F=yxp(gqwf)2SvDq_o=FHrg^Z4cr01LE03#39G(HSN6y+bn;Ma>NL)|X^NdptGWP'
            'EiFNjA9|pbQDB6Jq7LS3hz*Ibf<9L6E5A<L@85~Y5pH!h`&my)75yx{M3gu3l)ub{#aXHefgoo49y|)v6!M+tYM_'
            'uvT+I5<7YZ_ML5B1k#1`W?c+z^I~wV*1Af_kf*JZk^{G#@b0galoTWuJpC>1<r|HmcJi!fXeM3PktdX4Igi-U>H?'
            'TtnlF`N(!_7x(E_HWzx1Kqi`Wm4pet?*uLE|BKx3B|Fc|kU%&MMezYhB7BPIl2rqNBxI)9P9E6Uhv>q5QFg%}<qw'
            'bK<**{uT{iU}QJvW+2T(%e!xVFgsxVAhAX2XTTn9*HQrdtCjqA?l`+kt8Ng7tZJA@uH73LELN4sFt7!U@x6)LRLn'
            'FK+5I(d;8U+2dgk(weFfkUYgcqM59F2imV=PnloqOTh2w(pr}inGaS>X>CJ<|-w9$DtI4}vf6e&bZ6w*EfaZ{95s'
            '&j!u%W$xhjiv?^kQ)s#HbTL~jPeA>kfUKMZI;Ui@vz$#ux1>O{-fwuwJ$Kk!HKvbUM3l$Y?bSUL+`{#2@|S2G#Lb'
            'kx8jT@oia_Z^R9a(FL+^vc~-*_bixQ8g&Rzg`cW(}@8reu4QblWI314v0VjP)AcB^^beQv$WRM`z(_j60PR@a^`^'
            'EalV5Eq{4N|bB5ccF1bLzK)Ab}H%ej3P$zLGyEoFE^bANJxxiPMFt!XCjT#`l5SZ-fThK6g^uJ?9are*}8jK@7Yc'
            'PZ%A~*-}=b0DuBQK~JDq{^eiD33fA08!;c{pdV?=Vm+(T83aya@e5uOv5L&^%}k5)KRjRHAl?CeoBhN`{s2^|<t0'
            '}lz0WOUS{iu1!(lZr3bgm2?i>Kt&hf%`eWV?7F%e@^ga<GqUQsk`{vP!X(r0-TkKHC0u(n{CQw+Zw^U)&FOxVhvn'
            'FRp1`@HBm`G8x?3-vPWR;)imBv}GmZy`&km%km0zOI0<a8z~?uvCdi5@o|l_<ID9+w;3p!oxs!86N@=ybuZY62=x'
            'm^L+}YM$mp<>{XfzqJ;ZJ&=Bq#r1OIZX5UiMAH$2iNps<N)R0J!NK#)iI0CaPl=Q#Ii^b5~JH+)*BuH#erZ8VC0~'
            '+4R8C;T1$qplWn3b4uc2d^=fRkG*FbXC8el%;*y?#%cX_MDa>_214AM4%!ewy*L%kMw7pNBxWliKX(TbkKH$=eUM'
            '{|5~F9;MU%vuLJ*lDB`1W~~exOX>7q`Zn-_jfesDlJN%;lk5B`eevfO?UT9a?_ZMfCll*?iQ&g6UGXyyfagakA_i'
            'wj#(zk$4F3(KC;rdSHocF#BT2@84{V?okpXGQUu6KSWC2Cb&yx8Ibn@yd;hkrW(w={(R|CU$?EeGPlKGcFBZClM|'
            '3tzMN&Ik*?>+#)9u6m2WQ>}Cr;(yuDvf_G^PM-`!Q0&Sme$DNAEyD~4aaRnFo6Pon+gLFTv5m#GAV=KSp3P*-w<!'
            '-i$Lt?Cu=y-)dKvP3Zi&mRh%V<Kgs0zF1+!KIpA;_KWAr)@$+XOk-tt2FaA>&KZ7O_eoxng{SUf+ftj62^7x;<zd'
            '+gq;bf<V8}{DFYs78XcwOQC;)JV(t*{|zQceBno=Sqd?)8Dv{foUnLP~@UW)=0ePSOj<*DM)Px<3NLMeJj!Hgb&8'
            'PPQ0u3jVohP`SUe5rrm~I?d{*;=neQ`#S)|SUw3hxSiLi-Wm)15hN~Fub;pHs6ORdrAhtm5a8COUO(aLKhVbm(4p'
            'kbsjF}B0Zyki)PMN;6|BJdvRPz6ZEq|FU?|m8zvAm}FfOiQi;%|^KcR-ctT~rztiSQ~LujSz*~Vb`Vp$WD3EfX?t'
            '{(yqTnM2a@8Vj+%cV+AkIOeOoh#e5*FTB+Ekh@9saB$niwd?oM)lNhiTX1vLK5C?3{O3LrnS4f`%=vjb2z&f%PVx'
            '&pUL_;yvv6vh`Q%mb=S`Y^?z6-+$;y5_Ycpf{x5vLfL@vH=OFT&slqnj_Y2Yc3qw~9nSA+P&rN%4aW!MMcs{Rr;`'
            'bw(?zeqaR#thoYvjq_kDmSe*E4^=W8WVKp56Q7fAD_Fz5iwk-hVTn;`{FcEzti){{li>CSC'
        ),
    },
}
DIM_LICENSE = 'MIT License\n\nCopyright (c) 2018 Destiny Item Manager\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode()


def svg_polygons(path):
    """Parse the source's exact relative m/l/h/v/z polygon subset (no curves)."""
    tokens = re.findall(r'[mlhvz]|[-+]?(?:\d*\.\d+|\d+)', path)
    # Fail instead of silently approximating any future SVG command.
    assert not re.sub(r'[mlhvz\s,]|[-+]?(?:\d*\.\d+|\d+)', '', path)
    i, x, y, command, points, polygons = 0, 0.0, 0.0, None, [], []
    while i < len(tokens):
        if tokens[i] in ('m', 'l', 'h', 'v', 'z'):
            command = tokens[i]
            i += 1
        if command == 'z':
            assert len(points) >= 3
            polygons.append(points)
            x, y = points[0]
            points = []
            command = None
            continue
        if command in ('m', 'l'):
            x += float(tokens[i]); y += float(tokens[i + 1]); i += 2
            points.append((x, y))
            if command == 'm':
                command = 'l'
        elif command == 'h':
            x += float(tokens[i]); i += 1; points.append((x, y))
        elif command == 'v':
            y += float(tokens[i]); i += 1; points.append((x, y))
        else:
            raise ValueError('Unsupported path command')
    assert not points
    return polygons


def class_mask(path):
    polygons = svg_polygons(path)
    coords = [p for poly in polygons for p in poly]
    low_x, low_y = map(min, zip(*coords))
    high_x, high_y = map(max, zip(*coords))
    scale = 56 / max(high_x - low_x, high_y - low_y)
    center_x, center_y = (high_x + low_x) / 2, (high_y + low_y) / 2
    alpha = Image.new('L', (SIZE * SUPERSAMPLE,) * 2)
    draw = ImageDraw.Draw(alpha)
    for polygon in polygons:
        draw.polygon([((x - center_x) * scale * SUPERSAMPLE + 32 * SUPERSAMPLE,
                       (y - center_y) * scale * SUPERSAMPLE + 32 * SUPERSAMPLE)
                      for x, y in polygon], fill=255)
    return alpha.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def model_json(name):
    return {
        'gui_light': 'front',
        'textures': {'layer0': f'destiny:item/hud/{name}'},
        'elements': [{'from': [0, 0, 8], 'to': [16, 16, 8], 'faces': {
            side: {'texture': '#layer0', 'uv': [0, 0, 16, 16], 'tintindex': 0}
            for side in ('north', 'south')}}],
    }


def item_json(name):
    return {'model': {'type': 'minecraft:model', 'model': f'destiny:gui/hud/{name}',
                      'tints': [{'type': 'minecraft:custom_model_data', 'index': 0,
                                 'default': 16777215}]}}


def generate(root):
    root = Path(root)
    assets = []
    for name, source in SOURCE.items():
        if source['kind'] == 'dim_svg_path':
            assert sha256(source['svg_path'].encode()) == source['svg_path_sha256']
            alpha = class_mask(source['svg_path'])
            transform = 'Exact DIM polygon path; aspect-preserving 56px long axis, centered in 64px; 8x supersampling then Lanczos.'
        else:
            raw_alpha = zlib.decompress(base64.b85decode(source['alpha_zlib_b85']))
            assert len(raw_alpha) == 96 * 96
            assert sha256(raw_alpha) == source['source_alpha_sha256']
            alpha = Image.frombytes('L', (96, 96), raw_alpha).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
            transform = 'Exact Bungie 96x96 alpha embedded losslessly; full canvas Lanczos to 64x64; RGB fixed white.'
        image = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 0))
        image.putalpha(alpha)
        texture_path = f'src/main/resources/assets/destiny/textures/item/hud/{name}.png'
        model_path = f'src/main/resources/assets/destiny/models/gui/hud/{name}.json'
        item_path = f'src/main/resources/assets/destiny/items/gui/hud/{name}.json'
        target = root / texture_path
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, optimize=False, compress_level=9)
        for path, data in [(model_path, model_json(name)), (item_path, item_json(name))]:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(json_bytes(data))
        provenance = {k: v for k, v in source.items() if k not in ('svg_path', 'alpha_zlib_b85')}
        assets.append({'id': name, 'width': SIZE, 'height': SIZE, 'mode': 'RGBA',
                       'rgb': [255, 255, 255], 'manually_redrawn': False,
                       'pixel_identical_to_original': False, 'transform': transform,
                       'provenance': provenance,
                       'files': {p: sha256((root / p).read_bytes()) for p in (texture_path, model_path, item_path)},
                       'alpha_bbox': list(alpha.getbbox()),
                       'alpha_sha256': sha256(alpha.tobytes())})
    manifest = {'schema': 1, 'batch': 'W248', 'generator': 'scripts/generate_character_icons_w248.py',
                'generator_sha256': sha256(Path(__file__).read_bytes()),
                'offline': True, 'pillow_version': PIL.__version__,
                'tint': {'model_faces': ['north', 'south'], 'tintindex': 0,
                         'item_source': 'minecraft:custom_model_data', 'color_index': 0, 'default': 16777215},
                'accuracy': 'Source-derived masks, not hand reconstructions. DIM SVG is third-party reference, not a claimed official Bungie class download. PNG outputs are transformed, not byte-identical originals.',
                'third_party_notices': {'Destiny Item Manager': DIM_LICENSE,
                                        'Bungie': 'Destiny icon artwork belongs to Bungie. No ownership or original authorship claimed.'},
                'assets': assets}
    target = root / 'art/ui/w248/manifest.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(json_bytes(manifest))
    print(f'Generated {len(assets)} RGBA masks, 12 model/item JSONs and provenance manifest in {root}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Output repository root (default: parent of scripts/)')
    args = parser.parse_args()
    generate(args.root)
