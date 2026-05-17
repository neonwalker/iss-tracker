"""360x180 Natural Earth 1:110m land mask.

Vendored from NetOrbit (https://github.com/ZXCurban/NetOrbit), MIT-licensed.
The mask is one bit per 1-degree cell, row-major, lat top-down (90..-90), lon
left-to-right (-180..180).
"""

from __future__ import annotations

import base64
import zlib
from functools import lru_cache

MASK_WIDTH = 360
MASK_HEIGHT = 180

# --- BEGIN VENDORED FROM NetOrbit/src/netorbit/world_map.py ---
LAND_MASK_B85 = """
c-rlmJ8vCD6o6;%TAman6Dds)md8azg@h#vTv*<8{0(=MxFbSIW>ApQpxibE!bnIo`~fOF5(qa)<_93Mi4mrV<c(5f6R-Dh_A&3-8($DzMzVDu-<>&gUUTLwA#X-{G>{VlkX?jr0S*fMCoaI2V21bkl@weXmf^c|oWEZ}6$y3?Vczy|)-7Wgpb>kkLGav2p@cyy9<tRoxziNY0HaRGPLD|ZyLmT+;q(}wP<DUUhmTRBBf#HPu0DT;lYV2Zr;LVm%J0Ol`sIe9#9djz@RehgtwH<O5SZJkC47I>Pg#32b21wg%9NuL1>!`sIAym*qclaO7<R!`zZ@m9S1ZgB=KahATzBxeW7tO(Wu(keOiuPo5U)_n&dl8o)|GVupc`doUE&b8*1>cT3`LiZ92oUQHC(i(hmb41Ka}U_7{c+neR+7!%W>jPhx-xR8AFe(EfCJPicXiwab{nZa9QH^>Y@|*xp*0|W$Eoeq7<E*l@Oyi&)mFz&T7_qugnRlQbGt~RVmL7DQO3Xfg%Z)c99z6s2LmvcmmG51=|rW#al#;u!yGZ_Pqh0$`Muw>tHCF2%dEg%LXqNHcD0YfCn)7qW`XB<0esWV}2>~inYPsWdGgvY_u0TZK2_sg(_BJ2nTK4V;Cc?&g*Y|m<`FM^L=G3KX_5gBBRVC)A7^jnb{cCk&dZ><+*mi;gdg#1e`}nk&js<8mltSplf0FHE^7pKOFN~3_Dp`2L=;k8i~d%hUdbaxv*9&R$~}$>Z7P%XE7{@h0lOmnB_6NKD@ou;32RH_Z&6z2-b@=@Zt>6Lo9qR0c$BlbqcpCYJ6I_DK~_Rhh3Iq*03^*VEyxkZ#Aa~o0+-F-2=!RQ-h0cJv?#X7u213gfn~aFn8uTD>MI)cMg;05a^Ku7rf5A>cNHa99Ve(Hh1v#SMe$Dz-0Re$0T1v1Pl8PU;gHV>n|cIHn<~Ho;iNXDz7q7y3Ww>eeS@;o_Eko*Cu@d<fWKhA3h7<ARh%a1RQ)seG|daG>lerH-O`jpCDWlQnKU02Ucztz`rAW+e-`wAhfw@RH#w%o-UXMhX?U=gg*!?Duj2#{G^MfcLI2~%_a9>6he%8dD~!{qt&Pqo(pzW9_g)9T(WMV;dNb)8Cal_?t97@Bc@^NW#P&E5{-c+8We7150Tf*IcYukSr2EhpGU<gmUU%IUHBN+uYj}%*;WWE&qK$Gf>Z@*1&Ltd#H%i_NDo5-mL?O79(pSJ<F|zD`U1GI&Njex;(`#uxLq{`S9;eYEOrOD&8qk|QfBa(=SV0so~yeJ`7;4u8#71c!?(y^Sz?Ey_DUOi=!xYf`6;#`IUVz;a^jSCj`lbKKOHl)bmDXiYap3|l}>j~oL)yqllRgvjK1vz^;fi{Bn@Z7C8f1+O{;w3-j+GpU|{xGle!^R_6#cR5mPb9FQ+egxsy6Z;jmzufSHAbfzQ88-C<3_bS^iN!JWVJB&-E>awl)M)frhyT}+wTppMC+-T4vnE2)_aqjC-JsO|57uchEY4(TM?EzHHQ4&J{QT+eQhC-8CdGM#B((r|_HJP|67Etr6%5UZG(uB7ht5lp^0pyVW5OTp%JvzhkSE`4stE~<^(dTCi@v)N_>F6_)#?V6mX!h3|fm(0#pvNX&sY?J2;#$E&SZTkhok5@?+n$W^?djSXD!78$fh3^-RPVwWFy#=s2L_4^!C#GW+W>jb4D%I5~t&#C-bB*b<2$9($Sb4=twg7G&xEeAJjp5wF)Q4l4g%wkJFiYewX6#ce19Lxu_yyr|3N|6_tovHHx(J**)tDDSDL6B;<;%dC1J9GH6IM<)kh3=K+SLy1l)+f=H9$kRtF2^`c=cJ`Z6S}U*Yr>wOoN;|1<MY8H}0ZNz$oxe08e&XZw&nk7cM4StXSyEbsy%FaNQSIUa>X}R|xwXYT0zBH)wYvOc!;A>t*2EL7}^_PrVbsbcsHAY`_IeLG($!47^|nnJ*!;S^{pDdMdDt>Z)bnH{(By|II4FEph1Rt&D%+@H3L)eJbMEAD_obLeii!aob$V;>5P$!h8Kq#57SpiPDHoUmHV#>^v8U`W8jlb9@F#y6l_ZVO#Xv>p@!;vlR`i^y32!S39$+@0A3PyS%||rC8b@H))s#Jtnq5iau*@NdJl46f1)MF)nm9>ScK|oq7wka*FL`UUz;giTmUxsX42h_Oas)5O(j0{{&}WiAj-pq}Fqo9$6Oy4P0#St`k$joAGbPKhacx69
""".strip()
# --- END VENDORED ---


@lru_cache(maxsize=1)
def _mask_bytes() -> bytes:
    return zlib.decompress(base64.b85decode(LAND_MASK_B85.encode("ascii")))


def is_land_index(x: int, y: int) -> bool:
    """Look up a cell in the raw 360x180 grid (no clamping, no wrap)."""
    data = _mask_bytes()
    index = y * MASK_WIDTH + x
    return bool(data[index // 8] & (1 << (index % 8)))


def is_land(lat: float, lon: float) -> bool:
    """Look up a (lat, lon) coordinate. Wraps longitude, clamps latitude."""
    # Clamp lat to [-90, 90]
    if lat > 90.0:
        lat = 90.0
    elif lat < -90.0:
        lat = -90.0
    # Wrap lon to [-180, 180)
    lon = ((lon + 180.0) % 360.0) - 180.0

    x = int((lon + 180.0) / 360.0 * MASK_WIDTH)
    y = int((90.0 - lat) / 180.0 * MASK_HEIGHT)
    if x >= MASK_WIDTH:
        x = MASK_WIDTH - 1
    if y >= MASK_HEIGHT:
        y = MASK_HEIGHT - 1
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    return is_land_index(x, y)
