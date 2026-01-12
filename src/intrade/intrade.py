# %% [markdown]
# # InTrade v0.1.0

# %%
# Libraries needed Dic-25
import pandas as pd
import numpy as np
import os
import glob
import zipfile
import re
import itertools
import pyfixest as pf
import traceback
import statsmodels.api as sm

from scipy import optimize
from natsort import natsorted
from zipfile import ZipFile


# %%


# %% [markdown]
# ## Test: Dataset from other papers / Programs

# %%
def load_Test(typ):
    """
    Load a small synthetic input–output dataset for testing decomposition routines.

    This helper function builds toy multi-country, multi-sector input–output tables
    that can be used to test value-added decomposition algorithms (e.g. Decompr or
    WWZ-type decompositions).

    Parameters
    ----------
    typ : {"decompr", "WWZ"}
        Indicates which toy dataset to generate:
        - "decompr": three countries (ARG, TUR, DEU) and three sectors each.
        - "WWZ": three countries (rrr, sss, ttt) and two sectors each.

    Returns
    -------
    dict
        A dictionary with the following keys:
        - "df"  : pandas.DataFrame
            Square input–output matrix with intermediate use by country–sector
            plus final demand by country and total output.
            Rows are indexed by country–sector (e.g. "ARG_1") and columns are
            ordered as:
                * All country–sector intermediate demand blocks,
                * All country-specific final demand columns,
                * One total "Output" column.
        - "C"   : int
            Number of countries in the toy dataset.
        - "S"   : int
            Number of sectors per country.
        - "FD"  : int
            Number of final demand categories per country.
        - "CS"  : int
            Total number of country–sector pairs (C × S).
        - "CFD" : int
            Total number of country–final-demand pairs (C × FD).

    Notes
    -----
    The numeric values are arbitrary and are only meant to provide a consistent,
    reproducible example for unit tests and documentation examples. They should
    not be interpreted as empirical data.

    Examples
    --------
    >>> data = load_Test("decompr")
    >>> df = data["df"]
    >>> C, S = data["C"], data["S"]
    """

    # Example dataset compatible with "decompr"-style decompositions:
    # 3 countries (ARG, TUR, DEU), 3 sectors each, 1 final demand category.
    if typ == "decompr":
        data = {
            "Country":  ["ARG", "ARG", "ARG", "TUR", "TUR", "TUR", "DEU", "DEU", "DEU"],
            # Sectors are coded as "1", "2", "3" instead of industry abbreviations.
            "Industry": ["1", "2", "3",   "1", "2", "3",   "1", "2", "3"],
            "ARG_1": [16.1,  2.4, 0.9,  1.1, 0.3, 0.0,  1.2, 1.3, 2.1],
            "ARG_2": [ 5.1,  8.0, 0.5,  1.9, 2.8, 0.1,  4.2, 1.1, 1.4],
            "ARG_3": [ 1.8,  3.2, 4.0,  0.2, 0.1, 0.3,  0.3, 0.0, 3.0],
            "TUR_1": [ 3.2,  0.1, 0.0, 18.0, 6.1, 4.1,  4.1, 3.2, 4.1],
            "TUR_2": [ 4.3,  3.2, 0.1, 13.2,28.1, 3.2,  1.2, 4.8, 3.1],
            "TUR_3": [ 0.4,  1.6, 0.3,  6.1, 6.3, 8.9,  0.6, 2.6, 3.9],
            "DEU_1": [ 3.1,  1.2, 0.0,  9.0, 2.1, 0.2, 29.0, 5.1,11.3],
            "DEU_2": [ 2.8,  3.9, 0.4,  3.1, 2.5, 0.0, 19.5,29.1, 8.1],
            "DEU_3": [ 4.9, 11.5, 0.5,  8.9,25.6, 1.8, 17.9,24.1,51.3],
            # Country-specific final demand columns
            "ARG_4": [21.5,16.2,11.0,  7.5, 8.9, 1.2,  9.2, 7.9,25.1],
            "TUR_4": [ 6.1, 1.9, 0.5, 29.5,24.9,18.5, 17.9,10.1,35.2],
            "DEU_4": [ 8.4, 5.1, 0.8, 14.2,16.9, 4.9, 51.2,38.5,68.4],
            # Total output by country–sector
            "Output": [77.7,58.3,19.0,112.7,124.6,43.2,156.3,127.8,217.0],
        }

        # Create IO table with country–sector rows as index.
        df = pd.DataFrame(
            data,
            index=["ARG_1", "ARG_2", "ARG_3",
                   "TUR_1", "TUR_2", "TUR_3",
                   "DEU_1", "DEU_2", "DEU_3"],
        )

        # Reorder columns: all intermediate blocks, then final demand, then output.
        df = df[
            [
                "ARG_1", "ARG_2", "ARG_3",
                "TUR_1", "TUR_2", "TUR_3",
                "DEU_1", "DEU_2", "DEU_3",
                "ARG_4", "TUR_4", "DEU_4",
                "Output",
            ]
        ]

        # Number of countries, sectors and final-demand categories.
        C, S, FD = 3, 3, 1
        CS = C * S     # total country–sector combinations
        CFD = C * FD   # total country–final-demand combinations

        dic = {"df": df, "C": int(C), "S": int(S),
               "FD": int(FD), "CS": int(CS), "CFD": int(CFD)}

        print("load_Test, decompr: Done!")

    # Example dataset compatible with WWZ-style decompositions: WWZ 2018 NBER Quantifying...
    # 3 countries (rrr, sss, ttt), 2 sectors each, 1 final demand category.
    if typ == "WWZ":
        data = {
            "Country":  ["rrr", "rrr", "sss", "sss", "ttt", "ttt"],
            "Industry": ["1", "2",   "1", "2",   "1", "2"],
            # Intermediate input coefficients between country–sector pairs
            "rrr_1": [1, 1, 0, 0, 0, 0],
            "rrr_2": [1, 1, 0, 1, 0, 0],
            "sss_1": [0, 0, 1, 0, 1, 0],
            "sss_2": [0, 0, 1, 1, 0, 0],
            "ttt_1": [0, 0, 0, 0, 1, 1],
            "ttt_2": [0, 0, 0, 0, 0, 1],
            # Country-specific final demand columns
            "rrr_4": [1, 1, 1 / 10, 0, 0, 0],
            "sss_4": [0, 0, 9 / 10, 1, 1, 0],
            "ttt_4": [0, 1, 0, 0, 0, 1],
            # Total output by country–sector
            "Output": [3, 4, 3, 3, 3, 3],
        }

        # Create IO table with country–sector rows as index.
        df = pd.DataFrame(
            data,
            index=["rrr_1", "rrr_2", "sss_1", "sss_2", "ttt_1", "ttt_2"],
        )

        # Reorder columns: all intermediate blocks, then final demand, then output.
        df = df[["rrr_1", "rrr_2","sss_1", "sss_2","ttt_1", "ttt_2","rrr_4", "sss_4", "ttt_4", "Output",]]

        # Number of countries, sectors and final-demand categories.
        C = 3
        S = 2
        FD = 1
        CS = C * S     # total country–sector combinations
        CFD = C * FD   # total country–final-demand combinations

        dic = {"df": df, "C": int(C), "S": int(S),
               "FD": int(FD), "CS": int(CS), "CFD": int(CFD)}

        print("load_Test, WWZ: Done!")

    if typ == "exvatools":
        data = {
        # "Country":  ["ESP","ESP","ESP","FRA","FRA","FRA","MEX","MEX","MEX","USA","USA","USA","CHN","CHN","CHN","ROW","ROW","ROW","MX1","MX1","MX1","MX2","MX2","MX2","CN1","CN1","CN1","CN2","CN2","CN2","ESP","ESP","FRA","FRA","MEX","MEX","USA","USA","CHN","CHN","ROW","ROW"],
        # "Industry":,["1",,"2","3","1","2",  "3",   "1", "2","3",     "1", "2","3",     "1", "2","3",     "1", "2","3",    "1", "2","3",
        #     "1", "2",  "3",    "1", "2",  "3",   "1", "2","3",     "1", "2","3",     "1", "2","3",     "1", "2","3",    "1", "2","3",],

        "ESP_1":[11.78817398916,59.4016775600612,44.4643855274189,68.5215185289271,73.6351597954053,2.01818642602302,0,0,0,16.2448737751693,35.3043934255838,25.1073091651779,0,0,0,15.0473417325411,82.6552157953847,60.9953413074836,41.2652624903712,38.1793487400282,19.2483352259733,56.173100450309,55.6097120544873,23.4152981149964,18.1480179128703,58.7497136853635,42.9606631004717,20.3862804090604,70.8726119652856,27.5502263193484,26.2858421679121,6.58026722446084,41.9630978284404,11.5206921850331,25.2578474525362,9.83569126413204,71.0382958927657,6.69116413476877,88.0417850830127,34.1723352952395,32.827665773686,56.6112366421148],
        "ESP_2":[60.1372076368425,88.5663672348019,22.6647954361979,85.9039537920617,46.5446797469631,2.2195145203732,0,0,0,61.6310587320477,27.6725741708651,83.0729474131949,0,0,0,83.1035958337598,78.9239683165215,83.3523161537014,76.3062011941802,91.9011089727283,33.206104764482,56.3516501884442,6.79337786068209,82.0247998784762,86.8135506361723,27.80266667041,52.8868394391611,33.6375420512632,65.4439807725139,65.8349024790805,5.01902261655778,24.5134367661085,25.3803034326993,23.3266122255009,98.1122361768503,9.71667218906805,93.7114017670974,39.3856940164696,75.0543652672786,10.5258931254502,44.1598670918029,62.9060946961399],
        "ESP_3":[97.2904413149226,61.5433466227259,69.8016264894977,44.7286970023997,16.9538767901249,94.5252140103839,0,0,0,42.6563861391041,89.0126435244456,55.1999222794548,0,0,0,96.959178845631,82.8610785852652,15.5978680287953,27.9405590002425,90.5186752851587,85.9055693829432,67.3220810387284,97.7618970805779,39.9362385915592,55.2218770969193,11.9954458628781,68.2193691041321,6.6956547582522,55.0224263288546,95.3746928945184,91.9981481286231,69.8603930603713,63.6156065680552,90.6995727126487,49.5070160541218,45.009771206649,11.2930713114329,78.5470103032421,34.9635781326797,17.8422977994196,58.5745263309218,32.7429099951405],
        "FRA_1":[79.9402991987299,68.442522934638,40.2536409322638,84.7650818512775,34.351277786307,96.3780315355398,0,0,0,27.7529258795548,96.8581932361703,28.4586884465534,0,0,0,12.3395471740514,86.9512006388977,54.0214261340443,10.8578289842699,44.2044662514236,56.3185030072927,39.4071545677725,77.901521838503,95.5106799381319,74.9399329812732,50.2039153913502,22.8195718547795,45.3985951114446,15.2996740932576,19.6631224991288,18.2255278965458,18.8300572254229,81.5360131952912,82.568577688653,79.2156191896647,15.299199258443,16.0167959306855,32.6718650949188,36.1754500253592,26.079939178424,80.8224313436076,97.6933646788821],
        "FRA_2":[23.5564318839461,48.6812703821342,6.22054578410462,96.3773090029135,21.0933846149128,83.1644528994802,0,0,0,25.7042780865449,9.500821640715,63.7697545220144,0,0,0,36.7963224539999,67.8440181531478,94.7636352553964,65.1253874031827,84.7972347144969,48.0055431916844,47.4466128954664,60.7174228876829,64.7923324324656,81.4230900311377,57.6731397265103,28.1624812798109,78.1674579631072,5.20998986135237,53.3938483463135,72.8942679115571,29.1895917882212,9.77058009337634,75.6192006415222,97.1925470184069,65.2890822107438,15.8685097203124,48.1333893307019,57.2887228881009,9.14289528341033,31.2061208093073,35.5041553718038],
        "FRA_3":[52.3793174338061,52.2894875381608,34.4378520899918,81.2482898284215,69.3240501261316,1.1273083309643,0,0,0,91.9869063452352,46.4986468397547,61.5942499290686,0,0,0,36.7838723082095,23.0420184349641,69.7812815464567,33.0013585509732,25.15905465791,28.5517879487015,51.8753109809477,77.3235825216398,51.8451086746063,37.6217949115671,4.51799199497327,23.7934723969083,54.4140215411317,52.3758537212852,3.30590080237016,93.6312685746234,44.4369114697911,76.972126779845,76.2718317974359,43.5459824798163,43.9021138001699,20.1945080887526,17.5317955231294,9.8835463153664,41.444511226844,68.9700516439043,6.94075925718062],
        "MEX_1":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "MEX_2":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "MEX_3":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "USA_1":[91.7498587558512,12.7182002784684,79.8968587743584,68.6656810063869,73.1576954561751,55.1312441541813,0,0,0,42.9199172023218,34.6166953728534,95.1608482697047,0,0,0,59.8985969189089,61.9699287926778,32.7526820956264,2.75996532896534,69.078752696747,37.2743698719423,43.2636478657369,77.4475579271093,3.55501915374771,66.9978703965899,63.9509687058162,84.6222562873736,65.9648407495115,89.4404406722169,12.7661165511236,95.5340093562845,95.4843795062043,51.792491445085,62.657484118361,75.9658310473897,42.2472328271251,31.7816396902781,7.14483134355396,20.0303022805601,17.9002066941466,46.847343376372,22.5966310545336],
        "USA_2":[21.046750465408,61.4288340297062,80.246004168177,85.5779333608225,38.9906204787549,18.8857887028717,0,0,0,34.046952949604,55.7576032530051,49.6393310341518,0,0,0,7.10647771391086,81.6878863447346,78.821830218425,27.4349392615259,18.2067066431046,4.85009107249789,77.7654889018741,2.49489575484768,21.7929086822551,91.9468401984777,58.5891883771401,19.6408084898721,95.9180345020723,41.6597444668878,61.913576872088,65.6008500601165,56.5153064329643,11.317465903936,69.2123123432975,70.621769387275,12.6319594655652,89.7379705535714,94.7827477715909,16.1497451148462,15.0699020335451,85.2346356729977,47.080492710229],
        "USA_3":[17.3623880839441,50.3290329589508,57.9440643135458,76.8107536840253,86.6697056295816,65.2454654751346,0,0,0,13.7190884260926,55.9196835530456,77.5749846901745,0,0,0,49.8109536929987,37.188253023196,28.5821265971754,98.2728317421861,82.8513139530551,92.7710177861154,5.27498414437287,88.903145117918,48.7905999918003,38.6958371479996,46.4202894372866,34.8744207506534,80.6167861479335,88.7189863820095,37.0117520820349,73.5963430404663,6.88627021037973,49.5417880923487,78.5350041971542,96.9038471975364,68.741347294068,81.8145454658661,40.1680322720204,43.4152421304025,15.6671232627705,14.7739435788244,82.4527436487842],
        "CHN_1":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "CHN_2":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "CHN_3":[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        "ROW_1":[64.2245930514764,20.0759082282893,60.5000691183377,99.2297798055224,57.5154454249423,20.5287079645786,0,0,0,59.5684639110696,99.2122620658483,56.7166752340272,0,0,0,43.8975720282178,8.23586489842273,99.8379984856583,4.36863579275087,15.2102835120168,1.94949387130328,46.0100118040573,45.2845517981332,25.2435225620866,9.85680576227605,44.0042089095805,68.4588356541935,47.351113679586,24.4505732697435,37.2098288026173,71.4287080969661,99.3240842125379,17.7592745686416,2.77467803959735,9.55678159208037,30.2378128762357,66.8753522268962,14.4396189551335,18.5066452047322,27.9347330306191,11.6359583823942,39.8450227314606],
        "ROW_2":[20.0619958678726,14.3601599128451,80.0765763756353,6.46356638055295,38.3145183071028,19.4988366835751,0,0,0,27.6736478738021,4.99212649744004,75.6171301542781,0,0,0,86.17197126057,57.2506803674623,62.0845723571256,20.3510762250517,3.15172982122749,59.883764785016,42.690452033421,44.9235856912564,45.7356663779356,96.3535737392958,58.8263202381786,47.2390410460066,75.2087978916243,96.1528300836217,72.1561190516222,47.3369117160328,22.1959146352019,81.9792352828663,49.6260906341486,77.0501649826765,10.7690402215812,18.5424915913027,80.8837346618529,71.4277613547165,35.1613309283275,63.8506745111663,39.5758118601516],
        "ROW_3":[57.9815422417596,56.9925088984892,86.0088724859525,89.7894525590818,1.39518311852589,44.1609080403578,0,0,0,75.3923513283953,16.4480618159287,31.0081730778329,0,0,0,17.278994620312,44.9966754929628,80.3534769662656,6.84712445945479,52.1922088211868,72.5589441754855,83.1568011208437,65.9432429110166,25.4232154996134,47.9616010328755,87.0944682601839,69.758434477495,54.047669470543,69.7884489013813,11.6423549144529,70.4426843535621,67.5511357521173,31.0405726938043,70.4394817079883,57.5046685878187,6.5669236285612,97.8750601054635,30.8586008488201,18.8751542931423,22.5557930937503,14.4815771111753,71.541053276509],
        "MX1_1":[78.6743391950149,81.698482491076,6.17991075757891,61.144474129891,39.8587594260462,25.0405687578022,0,0,0,55.9075500483159,89.7445641420782,37.8801857957151,0,0,0,12.0229316530749,46.6046500701923,91.9677272599656,98.9354553818703,9.79094838630408,72.1638668805826,17.9581235873047,7.49604372098111,62.7011010614224,62.6465134748723,72.7405597330071,17.3604031130672,93.6008384167217,53.7707652149256,69.7541831615381,43.0980307147838,93.2541318759322,84.549935718067,91.7192413378507,56.6613778616302,78.1337355633732,36.4053636826575,52.3509084586985,56.8414282852318,84.4502549362369,15.462393553229,88.2269214254338],
        "MX1_2":[55.5301465892699,91.527964113513,46.1751471359748,41.215901290765,13.8891122976784,85.0680429900531,0,0,0,36.4831642145291,19.7943021859974,69.5605591468047,0,0,0,25.7486366939265,2.68300099042244,82.5041484360117,21.0321448231116,80.9675246356055,53.6315063519869,24.3448656816036,4.10820523952134,65.842924882425,95.5317376174498,15.773730155779,62.1858880920336,12.0866779503413,57.8688490267377,1.90545220463537,93.768481106963,20.0843756163958,20.1394581836648,2.82738631754182,44.9062999982852,96.3748821129557,23.3357709823176,43.2601660818327,98.2131952324416,97.3279389971867,64.0390123005491,68.9385919242632],
        "MX1_3":[59.7949674015399,15.8102237698622,32.2758852911647,70.3805248113349,66.1134208734147,29.5951683723833,0,0,0,69.5061879097484,90.7293306104839,7.35411580232903,0,0,0,90.7847771639936,35.0583554613404,3.13637075899169,59.7445268747397,8.62634062906727,76.7237540804781,66.8609496571589,82.2017968145665,1.75463941204362,10.7221291926689,33.2595127322711,10.3546248639468,68.2921707548667,18.0717369446065,99.826740982011,49.1252393894829,92.7315908223391,17.3598526273854,19.2617990288418,82.6966053943615,6.31897611380555,51.0878526461311,41.7282327273861,22.3448970778845,68.364775233902,3.22017506998964,44.408602348296],
        "MX2_1":[3.01967205875553,84.1247485021595,43.1715119094588,41.8190757038537,77.6391121230554,26.7122205507476,0,0,0,77.4734358021524,29.8352795913815,40.2045243417379,0,0,0,27.2329968553968,34.2641624014359,3.87846229225397,31.7756336983293,60.6255489434116,93.8924469696358,34.7951537859626,6.73479705164209,88.7905326017644,60.7241648966447,79.7765599733684,60.8127566489857,57.0396564688999,54.1098513945471,8.86097478982992,66.4605709929019,48.3384904486593,93.4735414264724,9.30016896431334,11.2599153481424,47.5838292080443,88.2716061244719,39.2588676428422,45.5869806148112,38.6333735731896,27.1062225291971,6.86052286881022],
        "MX2_2":[18.4865306948777,81.7836097471882,56.5822324638721,13.6401526241098,27.7749438085593,8.14651463204063,0,0,0,22.6413415006828,24.0077365359757,43.7293447840493,0,0,0,79.1364028893877,62.1616791922133,74.3401692190673,67.9462114796042,58.15796126239,16.5608965132851,6.10772528569214,25.4863307275809,67.9473074029665,85.7309065365698,47.216661159182,80.5883791781962,71.8832934426609,14.9159881086089,73.9847016071435,61.4906732197851,94.8880459645297,20.0932243936695,31.6995965554379,46.686989123933,26.64018391422,15.0429669134319,69.7613355107605,8.12784740026109,69.8578462400474,37.3152158772573,47.5543548050337],
        "MX2_3":[34.3114438245539,24.5287106116302,8.03340413863771,18.4391337439884,44.8005316497292,68.1382668798324,0,0,0,70.4528487690259,33.8881839769892,26.275988884503,0,0,0,19.5459923446178,55.5938125795219,32.365316440817,54.6189327021129,3.91998652764596,74.7057664175518,75.138456415385,7.03679817123339,13.5668472105172,99.6192908377852,30.0447192704305,62.5536412019283,24.3835663325153,98.776709344238,47.3702241212595,60.5999482013285,76.0469480699394,39.6562834070064,64.3445843392983,84.6272328097839,9.00331350974739,70.5971407426987,55.86924742884,37.149616451934,54.4156089646276,59.1305478489958,69.89823144814],
        "CN1_1":[53.7712868878152,69.5025723192375,34.1962522868998,53.5358478820417,6.07089391653426,73.6363335594069,0,0,0,49.2681732203346,74.2990421392024,30.3611934243236,0,0,0,78.1849004207179,80.6905396119691,81.9376330685336,44.8220697189681,38.5899669865612,86.9624725489412,51.9499235502444,87.4664943763055,99.6156701070722,87.4698988266755,18.663500016788,56.2652502136771,70.6978784238454,75.8158200341277,68.357165614143,25.0145588740706,17.5249546056148,85.8290661873762,18.2346866533626,35.5719059556723,13.9274826387409,96.9878384459298,89.2677422128618,72.0883486445528,67.9454108527862,72.075990077341,29.2657863872591],
        "CN1_2":[23.7101044268347,42.0949121804442,17.8886275475379,79.1798799405806,88.9898504852317,4.24891410046257,0,0,0,52.1528681574855,36.4666823523585,90.5547596653923,0,0,0,20.9944623240735,24.6580378203653,72.6397667312995,43.9280931884423,4.03407801594585,90.7103583549615,30.8825474369805,20.9200280252844,86.7958578760736,71.5001892228611,25.8929336233996,77.9472050967161,90.4016845384613,54.5249434609432,82.6990051772445,5.66532560740598,38.5956099834293,35.6469902019016,57.744654759299,11.9551744998898,86.1446765568107,61.0601698823739,99.0249628508464,96.445455658948,82.7266971748322,32.5200875347946,54.6154854244087],
        "CN1_3":[43.8006294758525,42.4504268378951,67.8756348218303,59.138739464106,90.8710218954366,61.9179187985137,0,0,0,35.2998148654588,39.7948886575177,80.1155185929965,0,0,0,48.6911596469581,27.9158485964872,37.7067476543598,81.1226886899676,52.0630656455178,54.4802003987134,58.5840718937106,23.5439860946499,73.4788895603269,30.6814490843099,86.1558804917149,59.6715195467696,14.466510118451,22.6168216532096,74.4967013509013,18.7682413621806,42.5359577727504,34.1265478730202,18.4002382494509,73.1050940852147,18.5940861280542,79.3513367299456,13.9938127750065,80.5964283659123,19.7070607624482,29.0255560907535,88.2279180944897],
        "CN2_1":[72.1710695715155,24.8086323963944,11.5797524389345,54.1797077325173,30.5938602476381,12.3920499822125,0,0,0,51.4168980517425,67.2088055748027,78.0004817242734,0,0,0,87.5290323572699,33.9750795317814,83.2343502207659,5.77833172935061,16.7689236970618,81.4346876409836,81.3638277188875,27.2449306529015,98.2288290304132,2.51636981358752,51.7538638173137,15.9391277993564,4.83468270581216,88.3488956787623,55.6487329653464,31.7530967933126,54.1555363815278,70.3844842652325,51.1582761351019,40.2930463440716,38.9334243203048,88.9042359702289,20.8883142690174,37.6033949702978,72.748338771984,47.5774232945405,20.782823698828],
        "CN2_2":[97.3448398204055,19.6039918037131,17.8489156598225,72.6894166811835,88.624668167904,36.6180112857837,0,0,0,14.3764516105875,39.5923479825724,24.5737852745224,0,0,0,69.9236002587713,33.9420775440522,84.9185744640417,57.7907150501851,97.7887024509255,79.7855722459499,41.4569124830887,18.6170228393748,61.724419208942,10.3091024041642,9.99186413502321,28.0605809909757,10.2163971301634,1.24866808811203,76.0364473515656,87.5165663990192,34.4082143760752,64.0040069709066,12.3726935253944,14.8499095886946,9.59625138319097,48.1279389415868,15.1000309248921,70.3792651852127,67.5053108041175,86.7607318093069,85.1098227372859],
        "CN2_3":[21.1168075017631,35.0337745307479,50.266977695981,59.896723004058,11.5909338076599,32.4622355049942,0,0,0,79.3740996655542,97.0591716123745,88.093757620547,0,0,0,35.7324976024684,56.3707266771235,91.9497757609934,93.0745289034676,17.5874662171118,62.0460999726783,47.8376084549818,17.3583834285382,30.9556536274031,58.2277166172862,23.4132843082771,31.1225874538068,59.4740063122008,98.3025121681858,40.8969069856685,82.1102421390824,99.1053192617837,42.3264187702443,26.0109641891904,94.2813475625589,2.62079048412852,70.305421779165,66.6710899530444,71.3537029821891,70.2021472123452,16.7818176981527,62.3161035415251],
        }

        df = pd.DataFrame(data, index=["ESP_1","ESP_2","ESP_3","FRA_1","FRA_2","FRA_2","MEX_1","MEX_2","MEX_3","USA_1","USA_2","USA_3","CHN_1","CHN_2","CHN_3","ROW_1","ROW_2","ROW_3","MX1_1","MX1_2","MX1_3","MX2_1","MX2_2","MX2_3","CN1_1","CN1_2","CN1_3","CN2_1","CN2_2","CN2_3","ESP_4","ESP_5","FRA_4","FRA_5","MEX_4","MEX_5","USA_4","USA_5","CHN_4","CHN_5","ROW_4","ROW_5"]).T


        df["MX1_4"]= df["MX1_5"] = df["MX2_4"] = df["MX2_5"] = df["CN1_4"]= df["CN1_5"] = df["CN2_4"] = df["CN2_5"] = 0

        df["output"] = df.sum(axis =1)

            # Number of countries, sectors and final-demand categories.
        C = 10
        S = 3
        FD = 2
        CS = C * S     # total country–sector combinations
        CFD = C * FD   # total country–final-demand combinations

        dic = {"df": df, "C": int(C), "S": int(S),
               "FD": int(FD), "CS": int(CS), "CFD": int(CFD)}

        print("load_Test, exvatools: Done!")

    return dic


# %%


# %% [markdown]
# ## ADB 

# %%
def load_ADB(dire, year, typ="LAC"):
    """
    Load an ADB MRIO table from Excel and convert country codes to ISO3.

    This function reads an Asian Development Bank (ADB) multi-regional input–output
    (MRIO) table from an Excel file, performs basic cleaning, infers the number of
    countries, sectors and final-demand categories, and converts ADB country codes
    to ISO3 (including regional aggregates such as RoW, RoL, etc.).

    Parameters
    ----------
    dire : str or pathlib.Path
        Directory where the ADB Excel files are stored. It should include the
        trailing separator (e.g. "path/to/ADB/").
    year : int
        Reference year of the ADB MRIO to load. The valid years depend on `typ`:
        - "LAC"    : typically 2007, 2011, 2017.
        - "CUR-62" : 2000, 2007, and annual series beyond 2007 depending on
                     the ADB releases used here.
        - "CUR-72" : years for which a 72-region ADB MRIO file exists in `dire`.
    typ : {"LAC", "CUR-62", "CUR-72"}, default "LAC"
        Variant of the ADB MRIO:
        - "LAC"    : Latin American MRIO with a focus on Latin American countries.
        - "CUR-62" : "Current" 62-region MRIO (ADB standard release).
        - "CUR-72" : "Current" 72-region MRIO.

    Returns
    -------
    dict
        Dictionary with:
        - "df"  : pandas.DataFrame
            Cleaned MRIO table with:
                * rows indexed by country–sector (e.g. "DEU_1"),
                * columns ordered as:
                    - all country–sector intermediate-use blocks,
                    - all final-demand columns,
                    - one total output column "OUT".
            All country codes are converted to ISO3 (plus a few regional
            aggregates such as "RoW" and "RoL").
        - "C"   : int
            Number of countries/regions.
        - "S"   : int
            Number of sectors per country.
        - "FD"  : int
            Number of final-demand components per country.
        - "CS"  : int
            Total number of country–sector pairs (C × S).
        - "CFD" : int
            Total number of country–final-demand pairs (C × FD).

    Notes
    -----
    - The function assumes that the ADB Excel files follow the standard layout:
      the IO matrix is stored in sheet "ADB MRIO {year}", with two header rows
      (country and industry) and two leading identifier columns.
    - ADB’s internal country codes (e.g. "SWI", "PRC", "SPA") are converted
      to ISO3 (e.g. "CHE", "CHN", "ESP") using a fixed mapping.
    - Regional aggregates like "RoW" and "RoL" are kept as such and treated as
      pseudo-ISO3 codes for convenience.
    """

    # ------------------------------------------------------------------
    # 1. Select file name and read the raw ADB MRIO Excel sheet
    # ------------------------------------------------------------------
    if typ == "LAC":
        # Latin American MRIO: filenames differ slightly by year
        if year == 2007:
            file = f"ADB-MRIO-LAC-{year}_Mar2022-1.xlsx"
        if year == 2011:
            file = f"ADB-MRIO-LAC-{year}_Mar2022.xlsx"
        if year == 2017:
            file = f"ADB-MRIO-LAC-{year}_Mar2022-2.xlsx"

        raw = pd.read_excel(
            dire + file,
            sheet_name=f"ADB MRIO {year}",
            skiprows=4,
            nrows=2557,
            usecols="C:DHM",
        )

    if typ == "CUR-62":
        # "Current" 62-region MRIO: filenames depend on the year
        if year == 2000:
            file = "ADB-MRIO-2000_Mar2022-3.xlsx"
        if year == 2007:
            file = "ADB-MRIO-2007.xlsx"
        if (year < 2017) and (year > 2007):
            file = f"ADB-MRIO-{year}_Mar2022.xlsx"
        if (year < 2020) and (year >= 2017):
            file = f"ADB-MRIO62-{year}_Dec2022.xlsx"
        if year >= 2020:
            file = f"ADB-MRIO62-{year}_June2023.xlsx"

        raw = pd.read_excel(
            dire + file,
            sheet_name=f"ADB MRIO {year}",
            skiprows=4,
            nrows=2207,
            usecols="C:CSC",
        )

    if typ == "CUR-72":
        # "Current" 72-region MRIO: search the file by pattern in `dire`
        pattern = f"ADB-MRIO-{year}" + "*" + ".xlsx"
        files = glob.glob(dire + pattern)

        if files:
            file = files[0]  # take the first file matching the pattern
            raw = pd.read_excel(
                file,
                sheet_name=f"ADB MRIO {year}",
                skiprows=4,
                nrows=2557,
                usecols="C:DHM",
            )
            print(f"File loaded: {file}")
        else:
            print("No file found matching the pattern for CUR-72.")
            # You may want to raise an error here in production code.
            # For now, this keeps the original behaviour.
    
    print(year, file)

    # ------------------------------------------------------------------
    # 2. Basic preparation of the ADB MRIO matrix
    # ------------------------------------------------------------------
    df = raw.copy()

    # Combine the first two header rows into one: "COUNTRY_SECTOR"
    df.columns = df.iloc[0, :] + "_" + df.iloc[1, :]
    df.columns = df.columns.str.replace("_c", "_", regex=False)

    # Build row index also as "COUNTRY_SECTOR"
    df.index = df.iloc[:, 0] + "_" + df.iloc[:, 1]
    df.index = df.index.str.replace("_c", "_", regex=False)

    # Drop the first two header rows and the first two identifier columns
    df = df.iloc[2:, 2:]

    # Rename the last column to "OUT" (total output)
    df.rename(columns={df.columns[-1]: "OUT"}, inplace=True)

    # ------------------------------------------------------------------
    # 3. Infer dimensions: number of sectors (S), countries (C), and FDs
    # ------------------------------------------------------------------
    # Trick: select a reference country and count how many sectors it has.
    # This assumes that all countries have the same number of sectors.
    ref = "AUS"

    # Number of sectors S: count how many rows belong to the reference country
    S = int(df.T.filter(like=ref).shape[1])
    # (In BEN notation: S = "k" for sector on the input side.)

    # Number of sectors plus final-demand categories for the reference country
    SplusFD = int(df.filter(like=ref).shape[1])
    FD = SplusFD - S   # number of final-demand components per country

    # If additional rows were present (e.g. extra aggregates), they can be
    # subtracted via `filas_adic`. Here we assume none.
    filas_adic = 0
    C = (df.shape[0] - filas_adic) / S  # number of countries
    CS = C * S                          # total country–sector rows
    CFD = C * FD                        # total country–FD columns

    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 4. Convert ADB country codes to ISO3 / ISO3-like codes
    # ------------------------------------------------------------------
    # ADB internal country codes (old_codes) and their ISO3 equivalents (new_codes).
    # Some entries correspond to regional aggregates (e.g. RoW, RoLAC/RoL).
    old_codes = [
        "AUS", "AUT", "BEL", "BGR", "BRA", "CAN", "SWI", "PRC", "CYP", "CZE",
        "GER", "DEN", "SPA", "EST", "FIN", "FRA", "UKG", "GRC", "HRV", "HUN",
        "INO", "IND", "IRE", "ITA", "JPN", "KOR", "LTU", "LUX", "LVA", "MEX",
        "MLT", "NET", "NOR", "POL", "POR", "ROM", "RUS", "SVK", "SVN", "SWE",
        "TUR", "TAP", "USA", "BAN", "MAL", "PHI", "THA", "VIE", "KAZ", "MON",
        "SRI", "PAK", "FIJ", "LAO", "BRU", "BHU", "KGZ", "CAM", "MLD", "NEP",
        "SIN", "HKG", "RoW",
        "ARG", "BOL", "CHL", "COL", "ECU", "PAR", "PER", "RoLAC", "URY", "VEN",
    ]

    new_codes = [
        "AUS", "AUT", "BEL", "BGR", "BRA", "CAN", "CHE", "CHN", "CYP", "CZE",
        "DEU", "DNK", "ESP", "EST", "FIN", "FRA", "GBR", "GRC", "HRV", "HUN",
        "IDN", "IND", "IRL", "ITA", "JPN", "KOR", "LTU", "LUX", "LVA", "MEX",
        "MLT", "NLD", "NOR", "POL", "PRT", "ROU", "RUS", "SVK", "SVN", "SWE",
        "TUR", "TWN", "USA", "BGD", "MYS", "PHL", "THA", "VNM", "KAZ", "MNG",
        "LKA", "PAK", "FJI", "LAO", "BRN", "BTN", "KGZ", "KHM", "MDV", "NPL",
        "SGP", "HKG", "RoW",
        "ARG", "BOL", "CHL", "COL", "ECU", "PRY", "PER", "RoL", "URY", "VEN",
    ]

    # Build mapping from ADB code to ISO3 / ISO-like code
    mapping = dict(zip(old_codes, new_codes))

    # Helper to replace the country code at the beginning of a "CODE_sector" label
    def replace_code(name, mapping):
        """
        Replace the leading ADB country code in a country–sector label with
        the corresponding ISO3 code, if it exists in `mapping`.
        """
        for old_code in mapping:
            if name.startswith(old_code):
                return name.replace(old_code, mapping[old_code], 1)
        return name

    # Apply the mapping to both columns and index
    df.columns = [replace_code(col, mapping) for col in df.columns]
    df.index = [replace_code(idx, mapping) for idx in df.index]

    # ------------------------------------------------------------------
    # 5. Natural sorting of country–sector blocks and final-demand columns
    # ------------------------------------------------------------------
    # We want sectors ordered as 1, 2, 3, 10, 11 (natural order),
    # not 1, 10, 11, 2, 3 (lexicographic string order).

    # First, sort columns within the country–sector block and within the FD block
    df = pd.concat(
        [
            df.iloc[:, : int(CS)][natsorted(df.iloc[:, : int(CS)].columns)],
            df.iloc[:, int(CS) : -1][natsorted(df.iloc[:, int(CS) : -1].columns)],
            df.iloc[:, -1],
        ],
        axis=1,
    )

    # Then, transpose and repeat the same logic for rows (if necessary)
    df = df.T
    df = pd.concat(
        [
            df.iloc[:, : int(CS)][natsorted(df.iloc[:, : int(CS)].columns)],
            df.iloc[:, int(CS) :],
        ],
        axis=1,
    )
    df = df.T

    # Ensure all entries are numeric (coerce non-numeric to NaN)
    # This is needed for some years/datasets where non-numeric junk may appear.
    df = df.apply(pd.to_numeric, errors="coerce")

    # ------------------------------------------------------------------
    # 6. Pack results into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# ## EORA
# 

# %%
def load_EORA(dire, year, typ="pp"):
    """
    Load an Eora26 MRIO table (T + FD) and infer basic dimensions.

    This function reads the Eora26 multi-regional input–output (MRIO) data
    for a given year and price concept (basic prices or purchaser prices),
    combines the intermediate transactions matrix (T) with the final demand
    matrix (FD), and infers the number of countries, sectors, and final-demand
    components.

    Country labels in Eora26 are already in ISO3 (plus some aggregates such as
    ROW), and are combined with sector labels to form keys like "USA_Agriculture".

    Parameters
    ----------
    dire : str or pathlib.Path
        Directory where the Eora26 zip files are stored. It should include the
        trailing separator (e.g. "path/to/EORA/raw/").
    year : int
        Reference year of the Eora26 MRIO to load (typically 1990–2016).
    typ : {"bp", "pp"}, default "pp"
        Price concept:
        - "bp" : basic prices.
        - "pp" : purchaser prices.

    Returns
    -------
    dict
        Dictionary with:
        - "df"  : pandas.DataFrame
            Combined MRIO table with:
                * rows = country–sector (plus possibly an aggregate like ROW),
                * columns = all country–sector intermediate-use entries
                  followed by all final-demand components.
        - "C"   : int
            Number of countries/regions (before dropping ROW).
        - "S"   : int
            Number of sectors per country.
        - "FD"  : int
            Number of final-demand components per country.
        - "CS"  : int
            Total number of country–sector rows (C × S).
        - "CFD" : int
            Total number of country–final-demand columns (C × FD).

    Notes
    -----
    - The function expects Eora26 files named like:
        * "Eora26_{year}_{typ}_T.txt"
        * "Eora26_{year}_{typ}_FD.txt"
        * "Eora26_{year}_{typ}_VA.txt"
      packaged in "Eora26_{year}_{typ}.zip", plus label files:
        * "labels_T.txt", "labels_FD.txt".
    - The ROW aggregate does not always have the full set of sectors. When this
      happens, ROW is removed from both rows and columns to keep a consistent
      square block of country–sector accounts.
    """

    # ------------------------------------------------------------------
    # 1. Open the zip file and read the relevant Eora26 text files
    # ------------------------------------------------------------------
    # Example structure:
    #   Eora26_2006_pp.zip
    #       ├─ Eora26_2006_pp_T.txt
    #       ├─ Eora26_2006_pp_FD.txt
    #       ├─ Eora26_2006_pp_VA.txt
    #       ├─ labels_T.txt
    #       └─ labels_FD.txt
    with zipfile.ZipFile(dire + f"Eora26_{year}_{typ}.zip", "r") as archivo_zip:
        # Final demand matrix
        with archivo_zip.open(f"Eora26_{year}_{typ}_FD.txt") as archivo_txt:
            df_FD = pd.read_csv(
                archivo_txt,
                delimiter="\t",
                encoding="utf-8",
                header=None,
            )

        # Intermediate transactions matrix
        with archivo_zip.open(f"Eora26_{year}_{typ}_T.txt") as archivo_txt:
            df_T = pd.read_csv(
                archivo_txt,
                delimiter="\t",
                encoding="utf-8",
                header=None,
            )

        # Value added (currently read but not used in this function)
        with archivo_zip.open(f"Eora26_{year}_{typ}_VA.txt") as archivo_txt:
            df_VA = pd.read_csv(
                archivo_txt,
                delimiter="\t",
                encoding="utf-8",
                header=None,
            )

        # Labels for FD and T
        with archivo_zip.open("labels_FD.txt") as archivo_txt:
            df_lFD = pd.read_csv(
                archivo_txt,
                delimiter="\t",
                encoding="utf-8",
                header=None,
            )

        with archivo_zip.open("labels_T.txt") as archivo_txt:
            df_lT = pd.read_csv(
                archivo_txt,
                delimiter="\t",
                encoding="utf-8",
                header=None,
            )

    print("Year:", year, "\nFile:", f"Eora26_{year}_{typ}")

    # ------------------------------------------------------------------
    # 2. Build country–sector labels for rows and columns
    # ------------------------------------------------------------------
    # Eora labels files typically have the structure:
    #   column 1 = country code (ISO3),
    #   column 3 = sector or component name.
    # We build labels as "ISO3_sector" for both T and FD.
    df_T.columns = list(df_lT[1] + "_" + df_lT[3])
    df_T.index = list(df_lT[1] + "_" + df_lT[3])

    df_FD.columns = list(df_lFD[1] + "_" + df_lFD[3])
    df_FD.index = list(df_lT[1] + "_" + df_lT[3])

    # Combine intermediate transactions (T) with final demand (FD)
    df = pd.merge(df_T, df_FD, left_index=True, right_index=True)

    # ------------------------------------------------------------------
    # 3. Infer number of sectors (S), final demand components (FD), etc.
    # ------------------------------------------------------------------
    ref = "USA"

    # Number of sectors S: count how many rows belong to the reference country.
    # (In BEN notation: S = "k" sector input side, "j" sector output side.)
    S = df.T.filter(like=ref).shape[1]

    # Total number of columns for the reference country (sectors + FD)
    SplusFD = int(df.filter(like=ref).shape[1])
    FD = SplusFD - S

    # Number of extra rows outside the country–sector block (e.g. ROW)
    filas_adic = 1  # Eora has one extra aggregate country (ROW)

    # Number of countries C, plus derived dimensions CS and CFD
    C = (df.shape[0] - filas_adic) / S
    CS = C * S
    CFD = C * FD

    # Alternative check using FD labels:
    # C0 = number of distinct country codes in the FD labels file.
    C0 = df_lFD[0].nunique()

    if C0 != C:
        print(
            "Warning: there is at least one country (e.g. ROW) that does not "
            "have the full set of sectors. Proceeding without that country."
        )

    # ------------------------------------------------------------------
    # 4. Drop ROW (or any aggregate starting with 'ROW') from rows & columns
    # ------------------------------------------------------------------
    df = df[~df.index.str.startswith("ROW")]
    df = df.loc[:, ~df.columns.str.startswith("ROW")]

    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 5. Pack results into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# ## FIGARO
# 
# 

# %%
def load_FIGARO(dire, year, typ="ind"):
    """
    Load a Eurostat FIGARO IC-IO matrix and convert country codes to ISO3.

    This function reads a Eurostat FIGARO inter-country input–output (IC-IO)
    matrix for a given year and layout (industry-by-industry or product-by-product),
    infers the number of countries, sectors and final-demand components, and
    standardises country codes to ISO3 using an internal ISO2→ISO3 mapping.

    FIGARO column/row labels are assumed to follow the pattern:
        CCxxx...  (where CC is a 2-letter country code, e.g. "US", "ES", "DE")
    plus a specific code for the rest of the world ("FIGW1"), which is renamed
    to "RW" for consistency.

    Parameters
    ----------
    dire : str or pathlib.Path
        Directory where the FIGARO CSV files are stored, e.g.
        ".../Figaro/raw/IO_industry" or ".../Figaro/raw/IO_product".
        It should NOT include a trailing slash for joining via '/' in this function.
    year : int
        Reference year of the FIGARO IC-IO data (e.g. 2010–2020).
    typ : {"ind", "prod"}, default "ind"
        Type of table:
        - "ind"  : industry-by-industry IO table.
        - "prod" : product-by-product IO table.

    Returns
    -------
    dict
        Dictionary with:
        - "df"  : pandas.DataFrame
            FIGARO IC-IO matrix with:
                * rows = country–sector (or country–product) plus extra rows,
                * columns = all country–sector blocks, followed by
                  final-demand components.
            All country codes are converted to ISO3, and sector/product codes
            are converted to a natural order index (1, 2, 3, 10, 11, ...).
        - "C"   : int
            Number of countries/regions.
        - "S"   : int
            Number of sectors (or products) per country.
        - "FD"  : int
            Number of final-demand components per country.
        - "CS"  : int
            Total number of country–sector combinations (C × S).
        - "CFD" : int
            Total number of country–final-demand combinations (C × FD).
    """

    # ------------------------------------------------------------------
    # 0. ISO2 → ISO3 mapping (local to this function)
    # ------------------------------------------------------------------
    iso2_to_iso3 = {
        'AF': 'AFG', 'AX': 'ALA', 'AL': 'ALB', 'DZ': 'DZA', 'AS': 'ASM', 'AD': 'AND', 'AO': 'AGO', 'AI': 'AIA', 
        'AQ': 'ATA', 'AG': 'ATG', 'AR': 'ARG', 'AM': 'ARM', 'AW': 'ABW', 'AU': 'AUS', 'AT': 'AUT', 'AZ': 'AZE', 
        'BS': 'BHS', 'BH': 'BHR', 'BD': 'BGD', 'BB': 'BRB', 'BY': 'BLR', 'BE': 'BEL', 'BZ': 'BLZ', 'BJ': 'BEN', 
        'BM': 'BMU', 'BT': 'BTN', 'BO': 'BOL', 'BQ': 'BES', 'BA': 'BIH', 'BW': 'BWA', 'BV': 'BVT', 'BR': 'BRA', 
        'IO': 'IOT', 'BN': 'BRN', 'BG': 'BGR', 'BF': 'BFA', 'BI': 'BDI', 'CV': 'CPV', 'KH': 'KHM', 'CM': 'CMR', 
        'CA': 'CAN', 'KY': 'CYM', 'CF': 'CAF', 'TD': 'TCD', 'CL': 'CHL', 'CN': 'CHN', 'CX': 'CXR', 'CC': 'CCK', 
        'CO': 'COL', 'KM': 'COM', 'CG': 'COG', 'CD': 'COD', 'CK': 'COK', 'CR': 'CRI', 'CI': 'CIV', 'HR': 'HRV', 
        'CU': 'CUB', 'CW': 'CUW', 'CY': 'CYP', 'CZ': 'CZE', 'DK': 'DNK', 'DJ': 'DJI', 'DM': 'DMA', 'DO': 'DOM', 
        'EC': 'ECU', 'EG': 'EGY', 'SV': 'SLV', 'GQ': 'GNQ', 'ER': 'ERI', 'EE': 'EST', 'ET': 'ETH', 'FK': 'FLK', 
        'FO': 'FRO', 'FJ': 'FJI', 'FI': 'FIN', 'FR': 'FRA', 'GF': 'GUF', 'PF': 'PYF', 'TF': 'ATF', 'GA': 'GAB', 
        'GM': 'GMB', 'GE': 'GEO', 'DE': 'DEU', 'GH': 'GHA', 'GI': 'GIB', 'GR': 'GRC', 'GL': 'GRL', 'GD': 'GRD', 
        'GP': 'GLP', 'GU': 'GUM', 'GT': 'GTM', 'GG': 'GGY', 'GN': 'GIN', 'GW': 'GNB', 'GY': 'GUY', 'HT': 'HTI', 
        'HM': 'HMD', 'VA': 'VAT', 'HN': 'HND', 'HK': 'HKG', 'HU': 'HUN', 'IS': 'ISL', 'IN': 'IND', 'ID': 'IDN', 
        'IR': 'IRN', 'IQ': 'IRQ', 'IE': 'IRL', 'IM': 'IMN', 'IL': 'ISR', 'IT': 'ITA', 'JM': 'JAM', 'JP': 'JPN', 
        'JE': 'JEY', 'JO': 'JOR', 'KZ': 'KAZ', 'KE': 'KEN', 'KI': 'KIR', 'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT', 
        'KG': 'KGZ', 'LA': 'LAO', 'LV': 'LVA', 'LB': 'LBN', 'LS': 'LSO', 'LR': 'LBR', 'LY': 'LBY', 'LI': 'LIE', 
        'LT': 'LTU', 'LU': 'LUX', 'MO': 'MAC', 'MK': 'MKD', 'MG': 'MDG', 'MW': 'MWI', 'MY': 'MYS', 'MV': 'MDV', 
        'ML': 'MLI', 'MT': 'MLT', 'MH': 'MHL', 'MQ': 'MTQ', 'MR': 'MRT', 'MU': 'MUS', 'YT': 'MYT', 'MX': 'MEX', 
        'FM': 'FSM', 'MD': 'MDA', 'MC': 'MCO', 'MN': 'MNG', 'ME': 'MNE', 'MS': 'MSR', 'MA': 'MAR', 'MZ': 'MOZ', 
        'MM': 'MMR', 'NA': 'NAM', 'NR': 'NRU', 'NP': 'NPL', 'NL': 'NLD', 'NC': 'NCL', 'NZ': 'NZL', 'NI': 'NIC', 
        'NE': 'NER', 'NG': 'NGA', 'NU': 'NIU', 'NF': 'NFK', 'MP': 'MNP', 'NO': 'NOR', 'OM': 'OMN', 'PK': 'PAK', 
        'PW': 'PLW', 'PS': 'PSE', 'PA': 'PAN', 'PG': 'PNG', 'PY': 'PRY', 'PE': 'PER', 'PH': 'PHL', 'PN': 'PCN', 
        'PL': 'POL', 'PT': 'PRT', 'PR': 'PRI', 'QA': 'QAT', 'RE': 'REU', 'RO': 'ROU', 'RU': 'RUS', 'RW': 'RWA', 
        'BL': 'BLM', 'SH': 'SHN', 'KN': 'KNA', 'LC': 'LCA', 'MF': 'MAF', 'PM': 'SPM', 'VC': 'VCT', 'WS': 'WSM', 
        'SM': 'SMR', 'ST': 'STP', 'SA': 'SAU', 'SN': 'SEN', 'RS': 'SRB', 'SC': 'SYC', 'SL': 'SLE', 'SG': 'SGP', 
        'SX': 'SXM', 'SK': 'SVK', 'SI': 'SVN', 'SB': 'SLB', 'SO': 'SOM', 'ZA': 'ZAF', 'GS': 'SGS', 'SS': 'SSD', 
        'ES': 'ESP', 'LK': 'LKA', 'SD': 'SDN', 'SR': 'SUR', 'SJ': 'SJM', 'SZ': 'SWZ', 'SE': 'SWE', 'CH': 'CHE', 
        'SY': 'SYR', 'TW': 'TWN', 'TJ': 'TJK', 'TZ': 'TZA', 'TH': 'THA', 'TL': 'TLS', 'TG': 'TGO', 'TK': 'TKL', 
        'TO': 'TON', 'TT': 'TTO', 'TN': 'TUN', 'TR': 'TUR', 'TM': 'TKM', 'TC': 'TCA', 'TV': 'TUV', 'UG': 'UGA', 
        'UA': 'UKR', 'AE': 'ARE', 'GB': 'GBR', 'US': 'USA', 'UM': 'UMI', 'UY': 'URY', 'UZ': 'UZB', 'VU': 'VUT', 
        'VE': 'VEN', 'VN': 'VNM', 'VG': 'VGB', 'VI': 'VIR', 'WF': 'WLF', 'EH': 'ESH', 'YE': 'YEM', 'ZM': 'ZMB', 
        'ZW': 'ZWE', 'AX': 'ALA', "RW": "ROW"
    }

    # ------------------------------------------------------------------
    # 1. Read FIGARO IC-IO CSV file
    # ------------------------------------------------------------------
    df = pd.read_csv(
        dire + "/matrix_eu-ic-io_" + typ + "-by-" + typ + "_24ed_" + str(year) + ".csv",
        index_col=0,
    )

    # Number of additional rows outside the country–sector block.
    # These usually correspond to various aggregates (e.g. taxes, VA, etc.).
    filas_adic = 6

    # ------------------------------------------------------------------
    # 2. Infer number of sectors (S) and final-demand components (FD)
    # ------------------------------------------------------------------
    ref = "US"  # reference country code in ISO2

    # Number of sectors S:
    # Count how many rows belong to the reference country in the transpose.
    S = int(df.T.filter(like=ref).shape[1])

    # Total number of columns for the reference country (sectors + FD)
    SplusFD = int(df.filter(like=ref).shape[1])
    FD = SplusFD - S

    # Number of countries C and related dimensions
    C = (df.shape[0] - filas_adic) / S  # countries/regions
    CS = C * S                           # total country–sector combinations
    CFD = C * FD                         # total country–FD combinations

    print(
        "Year:",
        year,
        "\nFile:",
        "matrix_eu-ic-io_" + typ + "-by-" + typ + "_24ed_" + str(year),
    )
    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 3. Harmonise rest-of-world code ("FIGW1" → "RW") in columns
    # ------------------------------------------------------------------
    for columna in df.columns:
        if columna.startswith("FIGW1"):
            new_name = "RW" + columna[len("FIGW1"):]
            df.rename(columns={columna: new_name}, inplace=True)

    # ------------------------------------------------------------------
    # 4. Build a mapping from FIGARO sector labels to sector indices 1..S
    # ------------------------------------------------------------------
    news_names = []
    for columna in df.filter(like=ref).columns:
        new_name = str(columna)[2:]  # remove first two characters (ISO2)
        news_names.append(new_name)

    diccionario_mapeo = {name: i + 1 for i, name in enumerate(news_names)}

    # ------------------------------------------------------------------
    # 5. Convert country codes from ISO2 to ISO3 in column labels
    # ------------------------------------------------------------------
    new_column_names = []
    for column_name in df.columns:
        first_two_letters = column_name[:2]
        new_first_two_letters = iso2_to_iso3.get(first_two_letters, first_two_letters)
        new_column_name = new_first_two_letters + column_name[2:]
        new_column_names.append(new_column_name)
    df.columns = new_column_names

    # ------------------------------------------------------------------
    # 6. Append sector indices (1..S) to column labels: "ISO3_sectorIndex"
    # ------------------------------------------------------------------
    for columna in df.columns:
        for parte_original, parte_nueva in diccionario_mapeo.items():
            if columna.endswith(parte_original):
                new_name = columna.rsplit(parte_original, 1)[0] + "_" + str(parte_nueva)
                df.rename(columns={columna: new_name}, inplace=True)

    # Transpose and repeat the process for row labels
    df = df.T

    # ------------------------------------------------------------------
    # 7. Harmonise "FIGW1" → "RW" and ISO2→ISO3 in row-side labels
    # ------------------------------------------------------------------
    for columna in df.columns:
        if columna.startswith("FIGW1"):
            new_name = "RW" + columna[len("FIGW1"):]
            df.rename(columns={columna: new_name}, inplace=True)

    new_column_names = []
    for column_name in df.columns:
        first_two_letters = column_name[:2]
        new_first_two_letters = iso2_to_iso3.get(first_two_letters, first_two_letters)
        new_column_name = new_first_two_letters + column_name[2:]
        new_column_names.append(new_column_name)
    df.columns = new_column_names

    for columna in df.columns:
        for parte_original, parte_nueva in diccionario_mapeo.items():
            if columna.endswith(parte_original):
                new_name = columna.rsplit(parte_original, 1)[0] + "_" + str(parte_nueva)
                df.rename(columns={columna: new_name}, inplace=True)

    # Transpose back to original orientation
    df = df.T

    # ------------------------------------------------------------------
    # 8. Natural ordering of country–sector blocks and FD components
    # ------------------------------------------------------------------
    df = pd.concat(
        [
            df.iloc[:, : int(CS)][natsorted(df.iloc[:, : int(CS)].columns)],
            df.iloc[:, int(CS):][natsorted(df.iloc[:, int(CS):].columns)],
        ],
        axis=1,
    )

    df = df.T
    df = pd.concat(
        [
            df.iloc[:, : int(CS)][natsorted(df.iloc[:, : int(CS)].columns)],
            df.iloc[:, int(CS):],
        ],
        axis=1,
    )
    df = df.T

    # ------------------------------------------------------------------
    # 9. Pack results into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# 
# 
# 
# ## GLORIA 
# 

# %%
def load_GLORIA(dire, year):
    """
    Load a GLORIA MRIO table (intermediate matrix T + final demand Y).

    This function reads a (very large) GLORIA MRIO for a given year from a
    compressed zip archive. It extracts:
      - the intermediate transactions matrix (T-Results),
      - the final demand matrix (Y-Results),

    and combines them into a single DataFrame with a consistent
    country–sector and country–final-demand structure.

    The GLORIA layout used here is:
      - C = 164 countries/regions,
      - S = 120 sectors per country,
      - FD = 6 final-demand components per country.

    Labels are constructed as:
      - "i_j" for country–sector (i = 1..C, j = 1..S),
      - "i_j" for country–final-demand (i = 1..C, j = S+1..S+FD).

    Parameters
    ----------
    dire : str or pathlib.Path
        Directory where the GLORIA zip file is stored. It should include the
        trailing separator, e.g. ".../Gloria/".
    year : int
        Reference year of the GLORIA MRIO to load (typically 1990–2028).

    Returns
    -------
    dict
        Dictionary with:
        - "df"  : pandas.DataFrame
            Combined matrix [T | Y] with:
                * rows  = country–sector indices "i_j" (i=1..C, j=1..S),
                * cols  = country–sector "i_j" for T, then "i_j" for FD.
        - "C"   : int
            Number of countries/regions (fixed at 164 in this implementation).
        - "S"   : int
            Number of sectors per country (fixed at 120).
        - "FD"  : int
            Number of final-demand components per country (fixed at 6).
        - "CS"  : int
            Total number of country–sector combinations (C × S).
        - "CFD" : int
            Total number of country–final-demand combinations (C × FD).

    Notes
    -----
    - GLORIA files are extremely large; reading them fully can be very slow.
      This implementation uses `skiprows` and `usecols` to select only the
      relevant blocks of rows/columns.
    - The function expects file names like:
        "GLORIA_MRIOs_59_{year}.zip"
      containing CSVs whose names match the patterns:
        "*Mother_AllCountries_002_T-Results_{year}_059_Markup001(full).csv"
        "*Mother_AllCountries_002_Y-Results_{year}_059_Markup001(full).csv"
    """

    num2cod = {1: "XAM", 2: "XEU", 3: "XAF", 4: "XAS", 5: "AFG", 6: "AGO", 7: "ALB", 8: "ARE", 9: "ARG", 10: "ARM",
            11: "AUS",12: "AUT",13: "AZE",14: "BDI",15: "BEL",16: "BEN",17: "BFA",18: "BGD",19: "BGR", 20: "BHR",
            21: "BHS",22: "BIH",23: "BLR",24: "BLZ",25: "BOL",26: "BRA",27: "BRN",28: "BTN",29: "BWA",30: "CAF",
            31: "CAN",32: "CHE",33: "CHL",34: "CHN",35: "CIV",36: "CMR",37: "COD",38: "COG",39: "COL",40: "CRI",
            41: "CUB",42: "CYP",43: "CZE",44: "DEU",45: "DJI",46: "DYE",47: "DNK",48: "DOM",49: "DZA",50: "ECU",
            51: "EGY",52: "ERI",53: "ESP",54: "EST",55: "ETH",56: "FIN",57: "FRA",58: "GAB",59: "GBR",60: "GEO",
            61: "GHA",62: "GIN",63: "GMB",64: "GNQ",65: "GRC",66: "GTM",67: "HND",68: "HKG",69: "HRV",70: "HTI",
            71: "HUN",72: "IDN",73: "IND",74: "IRL",75: "IRN",76: "IRQ",77: "ISL",78: "ISR",79: "ITA",80: "JAM",
            81: "JOR",82: "JPN",83: "KAZ",84: "KEN",85: "KGZ",86: "KHM",87: "KOR",88: "KWT",89: "LAO",90: "LBN",
            91: "LBR",92: "LBY",93: "LKA",94: "LTU",95: "LUX",96: "LVA",97: "MAR",98: "MDA",99: "MDG",100: "MEX",
            101: "MKD",102: "MLI",103: "MLT",104: "MMR",105: "MNG",106: "MOZ",107: "MRT",108: "MWI",109: "MYS",110: "NAM",
            111: "NER",112: "NGA",113: "NIC",114: "NLD",115: "NOR",116: "NPL",117: "NZL",118: "OMN",119: "PAK",120: "PSE",
            121: "PAN",122: "PER",123: "PHL",124: "PNG",125: "POL",126: "PRK",127: "PRT",128: "PRY",129: "QAT",130: "ROU",
            131: "RUS",132: "RWA",133: "SAU",134: "SDS",135: "SEN",136: "SGP",137: "SLE",138: "SLV",139: "SOM",140: "SRB",
            141: "SDN",142: "SVK",143: "SVN",144: "SWE",145: "SYR",146: "TCD",147: "TGO",148: "THA",149: "TJK",150: "TKM",
            151: "TUN",152: "TUR",153: "TZA",154: "UGA",155: "UKR",156: "URY",157: "USA",158: "UZB",159: "VEN",160: "VNM",
            161: "YEM",162: "ZAF",163: "ZMB",164: "ZWE",}

    # ------------------------------------------------------------------
    # 0. Fixed dimensions for the GLORIA MRIO
    # ------------------------------------------------------------------
    print("This takes a long time; Gloria is too big!!!")

    C = 164      # number of countries/regions
    S = 120      # number of sectors per country
    FD = 6       # number of final-demand components per country
    CS = 19680   # C * S
    CFD = 984    # C * FD

    # Build labels for country–sector and country–FD combinations
    names = [f"{num2cod[i]}_{j}" for i in range(1, C + 1) for j in list(range(1, S + 1))]
    names_fd = [f"{num2cod[i]}_{j}" for i in range(1, C + 1) for j in range(S + 1, S + FD + 1)]

    df1 = pd.DataFrame()
    df2 = pd.DataFrame()

    file = "GLORIA_MRIOs_59_" + str(year) + ".zip"

    # ------------------------------------------------------------------
    # 1. Patterns to detect T (intermediate) and Y (final demand) files
    # ------------------------------------------------------------------
    pattern = (
        r".*Mother_AllCountries_002_T-Results_"
        + str(year)
        + r"_059_Markup001\(full\)\.csv"
    )
    patternY = (
        r".*Mother_AllCountries_002_Y-Results_"
        + str(year)
        + r"_059_Markup001\(full\)\.csv"
    )

    # Rows/columns selection:
    # - rows : keep blocks where (i // S) % 2 == 0
    # - cols : keep blocks where (i // S) % 2 != 0
    # This exploits the GLORIA structure, where blocks are repeated for
    # different parts of the decomposition.
    rows = [i for i in range(0, int(C) * int(S) * 2) if (i // int(S)) % 2 == 0]
    cols = [i for i in range(0, int(C) * int(S) * 2) if (i // int(S)) % 2 != 0]

    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 2. Open zip file and read T and Y matrices
    # ------------------------------------------------------------------
    with zipfile.ZipFile(dire + file, "r") as archivo_zip:
        file_list = archivo_zip.namelist()
        matching_files = [f for f in file_list if re.match(pattern, f)]
        matching_filesFD = [f for f in file_list if re.match(patternY, f)]

        # Show which files were matched
        print(
            "Year:",
            year,
            "\nFile:",
            "GLORIA_MRIOs_59_" + str(year),
            "\n:",
            matching_files,
            "\n:",
            matching_filesFD,
        )

        # T matrix: intermediate transactions
        with archivo_zip.open(matching_files[0]) as archivo_txt:
            df1 = pd.read_csv(
                archivo_txt,
                skiprows=rows,
                usecols=cols,
                delimiter=",",
                encoding="utf-8",
                header=None,
            )

        # Y matrix: final demand
        with archivo_zip.open(matching_filesFD[0]) as archivo_txt:
            df2 = pd.read_csv(
                archivo_txt,
                skiprows=rows,
                delimiter=",",
                encoding="utf-8",
                header=None,
            )

    # ------------------------------------------------------------------
    # 3. Assign labels to rows and columns and combine [T | Y]
    # ------------------------------------------------------------------
    # T matrix: country–sector × country–sector
    df1.index = names
    df1.columns = names

    # Y matrix: country–sector × country–FD
    df2.index = names
    df2.columns = names_fd

    # Concatenate intermediate and final demand blocks
    df = pd.concat([df1, df2], axis=1)

    # ------------------------------------------------------------------
    # 4. Pack results into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# ##  TIVA - ICIO
# 
# 

# %%
def load_TIVA(dire, year, typ="extended"):
    """
    Load an OECD ICIO / TiVA table from compressed CSV files.

    This function reads the OECD Inter-Country Input–Output (ICIO) / TiVA
    database for a given year and layout ("small" or "extended"), performs
    some basic checks, reconstructs the "OUT" (total output) column if
    necessary, and infers the number of countries, sectors and final-demand
    components.

    For extended ICIO releases, it also merges split entries for Mexico and
    China (MEX = MX1 + MX2, CHN = CN1 + CN2) on both rows and columns, to
    keep a single ISO3-like code per country.

    Parameters
    ----------
    dire : str or pathlib.Path
        Directory where the ICIO zip files are stored. It should include the
        trailing separator (e.g. "path/to/ICIO/raw/").
    year : int
        Reference year of the ICIO/TiVA data to load. The function
        automatically selects the zip file that contains this year, based on
        the OECD file naming convention.
    typ : {"small", "extended"}, default "extended"
        Type of ICIO layout:
        - "small"    : smaller ICIO layout (e.g. aggregated dimensions).
        - "extended" : extended ICIO layout (more countries/sectors, split
                       entries for MEX/CHN, etc.).

    Returns
    -------
    dict
        A dictionary with:
        - "df"  : pandas.DataFrame
            ICIO table with:
                * rows = country–sector + extra rows (e.g. TLS, VA, OUT),
                * columns = all country–sector blocks, final-demand columns,
                  and (possibly) an "OUT" column for total output.
        - "C"   : int
            Number of countries in the ICIO.
        - "S"   : int
            Number of sectors per country.
        - "FD"  : int
            Number of final-demand components per country.
        - "CS"  : int
            Total number of country–sector combinations (C × S).
        - "CFD" : int
            Total number of country–final-demand combinations (C × FD).

    Notes
    -----
    - The function assumes that files are organised in multi-year zip archives:
      "ICIO-1995-2000-extended.zip", "ICIO-2016-2020-small.zip", etc.
    - For the "extended" layout, Mexico and China appear split into MX1/MX2
      and CN1/CN2. These are summed and collapsed into MEX and CHN, both in
      rows and columns.
    - The number of countries, sectors and final-demand components is inferred
      using a reference country ("USA") and the structure of the ICIO table.
      Three additional rows are assumed (TLS, VA, OUT), which are removed
      when computing C.
    """

    # ------------------------------------------------------------------
    # 1. Select the appropriate ICIO zip file based on the year
    # ------------------------------------------------------------------
    # ICIO releases are grouped into 5-year zip archives.
    if (year >= 1995) and (year <= 2000):
        file = f"ICIO-1995-2000-{typ}.zip"
    if (year >= 2001) and (year <= 2005):
        file = f"ICIO-2001-2005-{typ}.zip"
    if (year >= 2006) and (year <= 2010):
        file = f"ICIO-2006-2010-{typ}.zip"
    if (year >= 2011) and (year <= 2015):
        file = f"ICIO-2011-2015-{typ}.zip"
    if (year >= 2016) and (year <= 2020):
        file = f"ICIO-2016-2020-{typ}.zip"

    # ------------------------------------------------------------------
    # 2. Read the ICIO CSV from inside the zip archive
    # ------------------------------------------------------------------
    with zipfile.ZipFile(dire + file, "r") as archivo_zip:
        if typ == "small":
            # Small layout uses the suffix "_SML"
            with archivo_zip.open(f"{year}_SML.csv") as archivo_txt:
                df = pd.read_csv(
                    archivo_txt,
                    delimiter=",",
                    encoding="utf-8",
                    index_col=0,
                )
        if typ == "extended":
            # Extended layout uses the plain year name (e.g. "2018.CSV")
            with archivo_zip.open(f"{year}.CSV") as archivo_txt:
                df = pd.read_csv(
                    archivo_txt,
                    delimiter=",",
                    encoding="utf-8",
                    index_col=0,
                )

    print("Year:", year, "\nFile:", file)

    # Some ICIO releases come with an index name that may interfere with
    # later operations; reset it for consistency.
    df.index.name = None  # 21/11/2024: added to fix 2011–2015 issues

    # ------------------------------------------------------------------
    # 3. Check and reconstruct the "OUT" (total output) column if needed
    # ------------------------------------------------------------------
    # In some files, the "OUT" column is not present. The following check
    # compares the sum of all elements with the first element of the last
    # column to infer whether OUT is missing. If so, OUT is constructed as
    # the row sum.
    if int((df.sum().iloc[0] / 2 - df.iloc[0, -1])) != 0:
        # If the condition is non-zero, we assume there is no valid OUT column
        # and recompute OUT as the sum across columns.
        df["OUT"] = df.sum()  # add (or overwrite) OUT column

    # ------------------------------------------------------------------
    # 4. Infer number of sectors (S), final-demand components (FD), etc.
    # ------------------------------------------------------------------
    # We need a reference country and the number of "extra" rows (outside
    # the country–sector block) to back out C, S and FD.
    ref = "USA"

    # Number of sectors S:
    # Count how many rows belong to the reference country in the transpose.
    # (In BEN notation, S corresponds to "k" for sector on the input side.)
    S = int(df.T.filter(like=ref).shape[1])

    # Total number of columns for the reference country (sectors + FD)
    SplusFD = int(df.filter(like=ref).shape[1])
    FD = SplusFD - S  # number of final-demand columns per country

    # ------------------------------------------------------------------
    # 5. Collapse split entries for MEX and CHN in the extended layout
    # ------------------------------------------------------------------
    def mex_chn(df, MEX, MX1, MX2):
        """
        Collapse split country codes (e.g. MX1, MX2) into a single country code.

        Parameters
        ----------
        df : pandas.DataFrame
            ICIO matrix (either original or transposed).
        MEX : str
            Main country code (e.g. "MEX" or "CHN").
        MX1 : str
            First split code (e.g. "MX1" or "CN1").
        MX2 : str
            Second split code (e.g. "MX2" or "CN2").

        Returns
        -------
        pandas.DataFrame
            DataFrame where:
            - columns belonging to MX1 and MX2 have been summed into MEX,
            - MX1 and MX2 columns are removed.
        """
        print(df.shape)

        # Base block for the main country (MEX or CHN), restricted to the
        # sectoral part (first S columns for that country).
        df_t = df.filter(like=MEX).iloc[:, 0:S]

        # Blocks for the split parts MX1 and MX2, aligned to the same columns
        df_t1 = df.filter(like=MX1)
        df_t1.columns = df_t.columns
        df_t2 = df.filter(like=MX2)
        df_t2.columns = df_t.columns

        # Sum main + split parts
        df_t = df_t + df_t1 + df_t2

        # Replace main-country block with the summed values
        df[df_t.columns] = df_t[df_t.columns]

        # Drop split-country columns from the DataFrame
        df = df.drop(df.filter(regex=MX1, axis=1).columns, axis=1)
        df = df.drop(df.filter(regex=MX2, axis=1).columns, axis=1)

        return df

    if typ == "extended":
        # First collapse MEX/CHN as columns (destinations)
        df = mex_chn(df, "MEX", "MX1", "MX2")
        df = mex_chn(df, "CHN", "CN1", "CN2")
        # Then transpose and collapse them as rows (origins)
        df = df.T
        df = mex_chn(df, "MEX", "MX1", "MX2")
        df = mex_chn(df, "CHN", "CN1", "CN2")
        df = df.T

    # ------------------------------------------------------------------
    # 6. Compute number of countries and related dimensions
    # ------------------------------------------------------------------
    # Here we set the number of extra rows that are not country–sector:
    # typically "TLS", "VA", "OUT" (3 rows).
    filas_adic = 3  # TLS, VA, OUT

    # Number of countries C (in BEN notation: "i" or "n" depending on side)
    C = (df.shape[0] - filas_adic) / S
    CS = C * S      # total country–sector combinations
    CFD = C * FD    # total country–final-demand combinations

    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 7. Pack everything into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# ## WIOD
# 
# 

# %%
def load_WIOD(dire, year, typ):
    """
    Load a WIOD inter-country input–output table and infer basic dimensions.

    This function currently supports the WIOD 2016 release in Stata (.dta)
    format, using the ROW-extended tables (with rest-of-world).

    It reads the WIOT for a given year, builds country–sector row labels of
    the form "ISO3_sectorIndex", renames columns in a similar way, and
    infers the number of countries, sectors and final-demand components.

    Parameters
    ----------
    dire : str or pathlib.Path
        Base directory where WIOD files are stored. It should include the
        trailing separator, e.g. ".../WIOD/".
    year : int
        Reference year of the WIOT to load (e.g. 2000–2014 for WIOD 2016).
    typ : {"WIOD 2016", "WIOD 2013", "Long-run"}
        Type of WIOD dataset. Currently only "WIOD 2016" is implemented
        in this function. Other values will keep the original behaviour
        (and thus fail with an undefined DataFrame).

    Returns
    -------
    dict
        Dictionary with:
        - "df"  : pandas.DataFrame
            WIOD IO table with:
                * rows = country–sector (plus additional aggregate rows),
                * columns = country–sector blocks and final-demand columns,
                  named as "ISO3_sectorIndex" (e.g. "USA_1", "DEU_5", ...).
        - "C"   : int
            Number of countries/regions in WIOD (including ROW).
        - "S"   : int
            Number of sectors per country.
        - "FD"  : int
            Number of final-demand components per country.
        - "CS"  : int
            Total number of country–sector combinations (C × S).
        - "CFD" : int
            Total number of country–final-demand combinations (C × FD).

    Notes
    -----
    - For WIOD 2016, the function expects a file:
        "WIOD 2016/WIOT{year}_October16_ROW.dta"
      inside the directory `dire`.
    - Row index is built as "Country_RNr", where:
        * Country = 3-letter WIOD country code (ISO3-like),
        * RNr     = running sector/row number (converted to string).
    - Column names originally start with 'v' (e.g. 'vUSA01') and are
      transformed into "USA_01" (ISO3 + '_' + sector index).
    """

    # ------------------------------------------------------------------
    # 1. Load WIOD 2016 table from Stata file
    # ------------------------------------------------------------------
    if typ == "WIOD 2016":
        df = pd.read_stata(
            dire + "WIOD 2016\\WIOT" + str(year) + "_October16_ROW.dta"
        )

        # Build index as "Country_RNr"
        df = df.set_index(df["Country"] + "_" + df["RNr"].astype(str))

        # Drop metadata columns not needed in the IO matrix
        df = df.drop(
            columns=["IndustryCode", "IndustryDescription", "Country", "RNr", "Year"]
        )

        # Original WIOD column names for flows usually start with 'v' (e.g. "vUSA01"):
        # remove leading 'v' if present.
        df = df.rename(columns=lambda x: x[1:] if isinstance(x, str) and x.startswith("v") else x)

        # Then split into "ISO3_sectorIndex": first 3 chars as ISO3, rest as sector index.
        df.columns = [col[:3] + "_" + col[3:] for col in df.columns]

    # Simple head call (useful for debugging; can be removed in production)
    df.head()

    # ------------------------------------------------------------------
    # 2. Infer number of sectors (S), final-demand components (FD), etc.
    # ------------------------------------------------------------------
    ref = "USA"  # reference country (ISO3 code in WIOD)

    # Number of sectors S: count how many rows belong to the reference country
    S = int(df.T.filter(like=ref).shape[1])

    # Total number of columns for the reference country (sectors + FD)
    SplusFD = int(df.filter(like=ref).shape[1])
    FD = SplusFD - S

    # Number of additional rows (aggregates, totals, etc.) outside C×S
    filas_adic = 8

    # Number of countries C and related dimensions
    C = (df.shape[0] - filas_adic) / S
    CS = C * S
    CFD = C * FD

    print("Year:", year, "\nFile:", "WIOD\\WIOT" + str(year) + "_October16_ROW")
    print("\n Num Countries", C, "\n Num sect", S, "\n Num components FD", FD)

    # ------------------------------------------------------------------
    # 3. Pack results into a dictionary
    # ------------------------------------------------------------------
    dic = {
        "df": df,
        "C": int(C),
        "S": int(S),
        "FD": int(FD),
        "CS": int(CS),
        "CFD": int(CFD),
    }

    print("Done!")

    return dic


# %%


# %% [markdown]
# ## Aggregate country level

# %%
def aggregate(d):
    """
    This function aggregates IO table to the country level, collapsing all sectors and final-demand categories so that: 
    - each country has one sector
    - each country has one final-demand category
    - the output is a country × country IO table

    Parameters
    ----------
    dic : dict
    
    Returns
    -------
    dic : dict
    """
    # Interm
    Z = d["df"].iloc[:d["CS"], :d["CS"]].copy()
    
    # Extraer país
    row_country = Z.index.to_series().str.split("_").str[0]
    col_country = Z.columns.to_series().str.split("_").str[0]
    
    # Agregar filas
    Z_agg = Z.groupby(row_country).sum()
    
    # Agregar columnas (forma future-proof)
    Z_agg = (Z_agg.T.groupby(col_country).sum().T)
    
    # Renombrar como pais_1
    Z_agg.index   = Z_agg.index.astype(str) + "_1"
    Z_agg.columns = Z_agg.columns.astype(str) + "_1"

    # Final
    
    F = d["df"].iloc[:d["CS"], d["CS"]:d["CS"]+d["CFD"]].copy()
    
    # Extraer país
    row_country = F.index.to_series().str.split("_").str[0]
    col_country = F.columns.to_series().str.split("_").str[0]
    
    # Agregar filas
    F_agg = F.groupby(row_country).sum()
    
    # Agregar columnas (forma future-proof)
    F_agg = (F_agg.T.groupby(col_country).sum().T)
    
    # Renombrar como pais_1
    F_agg.index   = F_agg.index.astype(str) + "_1"
    F_agg.columns = F_agg.columns.astype(str) + "_2"

    ZF_agg = pd.concat([Z_agg, F_agg], axis=1)

    dic = {
        "df": ZF_agg,
        "C": d["C"],
        "S": 1,
        "FD": 1,
        "CS": d["C"],
        "CFD": d["C"],
    }

    print("Done!")
    
    return dic


# %%


# %% [markdown]
# # 2- Create inputs
# 
# 
# <hr style="border:1px solid blue; margin-top: 0; margin-bottom: 0;">
# 
# 
# 

# %% [markdown]
# ## Create I-O input

# %%
def obj_IO(dic):
    """
    Build a full input–output object from a harmonised MRIO dictionary.

    This function takes as input the harmonised dictionary returned by the
    loader functions (with keys "df", "C", "S", "FD", "CS", "CFD") and
    constructs a collection of NumPy arrays commonly used in input–output
    and trade-in-value-added analysis, including:

    - Z, Zd, Zm : intermediate input matrix and its domestic/foreign splits.
    - A, Ad, Am : technical coefficients matrix and its domestic/foreign splits.
    - B, Bd, Bm : global Leontief inverse and its domestic/foreign splits.
    - L         : local domestic Leontief inverse using only Ad.
    - Y, Yd, Ym : final demand by country and its domestic/foreign splits.
    - X, VA     : gross output and value-added in levels.
    - V, W      : value-added coefficients vector and its diagonal matrix.
    - EXGR, E   : gross bilateral exports and diagonal total-export matrix.
    - Efd, Eint, ESR : exports of final goods, intermediates and total exports.

    It also returns dimension and name metadata in nested dictionaries
    ("dims" and "names") to facilitate use in further analysis.

    Parameters
    ----------
    dic : dict
        Dictionary with at least the following keys:
        - "df"  : pandas.DataFrame, MRIO table in harmonised format.
        - "C"   : int, number of countries/regions.
        - "S"   : int, number of sectors per country.
        - "FD"  : int, number of final-demand components per country.
        - "CS"  : int, C × S.
        - "CFD" : int, C × FD.

    Returns
    -------
    io_dic : dict
        Dictionary containing IO-related matrices as NumPy arrays:
        {
            "Z", "Zd", "Zm",
            "A", "Ad", "Am",
            "B", "Bd", "Bm",
            "L",
            "Y", "Yd", "Ym",
            "Yfd",
            "VA", "V", "W",
            "X",
            "EXGR", "E", "Efd", "Eint", "ESR",
            "dims": {...},
            "names": {...}
        }
    """

    # Unpack core elements from the MRIO dictionary
    df, C, S, FD, CS, CFD = (
        dic["df"],
        dic["C"],
        dic["S"],
        dic["FD"],
        dic["CS"],
        dic["CFD"],
    )

    # ------------------------------------------------------------------
    # 1. Create base block-diagonal structures for domestic/foreign splits
    # ------------------------------------------------------------------
    # Block selector for domestic country–sector pairs (CS×CS)
    block_diag1_CSxCS = np.kron(np.identity(C), np.ones((S, S)))
    # Complement for foreign links (CS×CS)
    block_diag0_CSxCS = np.ones((C * S, C * S)) - block_diag1_CSxCS

    # Block selector for domestic country blocks in (CS×C)
    block_diag1_CSxC = np.kron(np.identity(C), np.ones((S, 1)))
    # Complement for foreign contributions in (CS×C)
    block_diag0_CSxC = np.ones((S * C, C)) - block_diag1_CSxC

    # Block selector for combined [CS×(CS+C)] structures if needed
    block_diag1_CSxCSC = np.concatenate([block_diag1_CSxCS, block_diag1_CSxC], axis=1)
    block_diag0_CSxCSC = np.ones((S * C, S * C + C)) - block_diag1_CSxCSC

    # ------------------------------------------------------------------
    # 2. Extract Z (intermediate) and Yfd (detailed final demand) blocks
    # ------------------------------------------------------------------
    Z = df.iloc[: S * C, : S * C]  # CS×CS intermediate inputs
    Yfd = df.iloc[: S * C, S * C : (S + FD) * C]  # CS×(C×FD) final demand

    # ------------------------------------------------------------------
    # 3. Build name vectors for countries, sectors and final demand
    # ------------------------------------------------------------------
    # Country codes (ISO3) from column labels "ISO3_sector"
    c_names = (
        Z.columns.str.split("_", n=1, expand=True)
        .get_level_values(0)
        .unique()
        .astype(str)
    )
    # Sector indices (as strings) from the second part of "ISO3_sector"
    s_names = (
        Z.columns.str.split("_", n=1, expand=True)
        .get_level_values(1)
        .unique()
        .astype(str)
    )
    cs_names = Z.columns  # full country–sector labels

    # Final-demand labels (second part of "ISO3_fdLabel")
    fd_names = (
        Yfd.columns.str.split("_", n=1, expand=True)
        .get_level_values(1)
        .unique()
        .astype(str)
    )
    cfd_names = Yfd.columns  # full country–final-demand labels

    # ------------------------------------------------------------------
    # 4. Value-added (VA) and gross output (X) as level vectors
    # ------------------------------------------------------------------
    # Value added (CS×1): total uses (intermediate + FD) minus intermediate inputs
    # VA = total exports to final demand by country–sector
    VA = pd.DataFrame(
        df.iloc[: S * C, : (S + FD) * C].sum(axis=1)
        - df.iloc[: S * C, : S * C].sum(axis=0),
        columns=["VA"],
    ).iloc[:, 0]

    # Gross output (CS×1): total outflows (intermediate + final demand)
    X = pd.DataFrame(df.iloc[: S * C, : (S + FD) * C].sum(axis=1)).iloc[:, 0]

    # Ensure first element is numeric (defensive cast for some datasets)
    X.iloc[0] = pd.to_numeric(X.iloc[0])

    # ------------------------------------------------------------------
    # 5. Intermediate matrix Z and its domestic/foreign components
    # ------------------------------------------------------------------
    # Convert Z to a NumPy array
    Z = Z.values.copy()  # CS×CS matrix of intermediate inputs

    # Domestic intermediate flows (within the same country block)
    Zd = Z * block_diag1_CSxCS
    # Foreign intermediate flows (across countries)
    Zm = Z * block_diag0_CSxCS

    # ------------------------------------------------------------------
    # 6. Technical coefficients A and Leontief inverses
    # ------------------------------------------------------------------
    # Invert X as a diagonal matrix, using pseudo-inverse to handle zeros
    x_hat_inv = np.linalg.pinv(np.diag(X))

    # Technical coefficients matrix A (CS×CS)
    A = Z @ x_hat_inv

    # Domestic and foreign parts of A
    Ad = A * block_diag1_CSxCS  # domestic (block-diagonal) part
    Am = A * block_diag0_CSxCS  # foreign (off-block) part

    # Local Leontief inverse using only domestic A (Ad)
    L = np.linalg.inv(np.identity(S * C) - Ad)

    # Global Leontief inverse B = (I − A)⁻¹
    B = np.linalg.inv(np.eye(CS) - A)
    Bd = B * block_diag1_CSxCS  # domestic part of the Leontief inverse
    Bm = B * block_diag0_CSxCS  # foreign part of the Leontief inverse

    # ------------------------------------------------------------------
    # 7. Final demand by country Y (CS×C) and domestic/foreign splits
    # ------------------------------------------------------------------
    # Aggregate detailed final-demand columns by destination country
    Y = (
        Yfd.T.groupby(
            Yfd.columns.str.split("_", n=1, expand=True).get_level_values(0)
        )
        .sum()
        .T
    )

    # Ensure country order in Y matches c_names
    Y = Y[c_names]

    # Convert to NumPy
    Y = Y.values.copy()

    # Domestic contents of final demand (diagonal country blocks)
    Yd = Y * block_diag1_CSxC
    # Foreign contents of final demand
    Ym = Y * block_diag0_CSxC

    # ------------------------------------------------------------------
    # 8. Value-added coefficients and diagonal value-added matrix
    # ------------------------------------------------------------------
    # WWZ-style value-added coefficients: V = u [I − A]
    V = (np.ones((1, S * C)) @ (np.identity(S * C) - A)).T  # (CS×1)
    V[np.isnan(V)] = 0  # clean potential NaNs

    # Diagonal matrix of value-added coefficients
    W = np.diag(V.squeeze())

    # ------------------------------------------------------------------
    # 9. Gross bilateral exports (EXGR) and total exports diagonal (E)
    # ------------------------------------------------------------------
    # Zm_meld aggregates foreign intermediate flows by partner country
    Zm_meld = np.zeros((CS, C))

    for i in range(1, C + 1):
        m = S * (i - 1)  # row start for origin country i
        n = S * i        # row end for origin country i
        for j in range(1, C + 1):
            p = S * (j - 1)  # col start for destination country j
            q = S * j        # col end for destination country j
            # Sum foreign intermediate exports from i to j by sector
            Zm_meld[m:n, j - 1] = Zm[m:n, p:q].sum(axis=1)

    # Gross bilateral exports EXGR (CS×C):
    # intermediate exports (Zm_meld) + final goods exports (Ym)
    EXGR = Zm_meld + Ym

    # Diagonal matrix of total exports by country–sector (E-hat)
    E = np.diag(EXGR.sum(axis=1))

    # ------------------------------------------------------------------
    # 10. Decomposition of exports into final (Efd), intermediate (Eint), total (ESR)
    # ------------------------------------------------------------------
    # Stack intermediate and final demand horizontally (CS×(CS+C))
    z = np.hstack((Z, Y))

    # Initialize matrices for export decomposition (CS×C)
    Efd = np.zeros_like(Y)   # exports of final goods
    ESR = np.zeros_like(Y)   # total exports
    Eint = np.zeros_like(Y)  # exports of intermediates

    # Compute Efd (final exports), Eint (intermediate exports), and ESR (total)
    for i in range(C):
        # Row block for sectors of origin country i
        m = i * S
        n = (i + 1) * S

        # Column ranges for final demand of destination country i
        s = CS + (i * FD)
        r = CS + FD + (i * FD)

        # Final-goods exports by origin sector and destination i
        if s == r:
            Efd[:, i] = z[:, s]
        else:
            Efd[:, i] = np.sum(z[:, s:r], axis=1)

        # Intermediate exports by origin sector to destination i
        Eint[:, i] = np.sum(z[:, m:n], axis=1)

        # Total exports
        ESR[:, i] = Eint[:, i] + Efd[:, i]

    # ------------------------------------------------------------------
    # 11. Convert key pandas objects to NumPy arrays
    # ------------------------------------------------------------------
    VA = VA.values.copy()
    X = X.values.copy()
    Yfd = Yfd.values.copy()

    # ------------------------------------------------------------------
    # 12. Build the IO object dictionary
    # ------------------------------------------------------------------
    io_dic = {
        "Z": Z,
        "Zd": Zd,
        "Zm": Zm,
        "A": A,
        "Ad": Ad,
        "Am": Am,
        "B": B,
        "Bd": Bd,
        "Bm": Bm,
        "Y": Y,
        "Yd": Yd,
        "Ym": Ym,
        "L": L,
        "Yfd": Yfd,
        "VA": VA,
        "V": V,
        "W": W,
        "X": X,
        "EXGR": EXGR,
        "E": E,
        "Efd": Efd,
        "Eint": Eint,
        "ESR": ESR,
    }

    # Dimension metadata
    io_dic["dims"] = {"C": C, "S": S, "FD": FD, "CS": CS, "CFD": CFD}

    # Name metadata
    io_dic["names"] = {
        "c_names": c_names,
        "s_names": s_names,
        "fd_names": fd_names,
        "cs_names": cs_names,
        "cfd_names": cfd_names,
    }

    print("Input Output Object Done!")
    return io_dic


# %%


# %% [markdown]
# ## Create Obj. Gravity input & Obj. panel

# %%
def obj_Grav(dic):
    """
    Build bilateral trade flows by exporter–sector–importer for gravity models.

    This function takes a harmonised MRIO dictionary (as returned by the loader
    functions) and aggregates both intermediate and final goods exports into a
    panel-style DataFrame suitable for gravity estimation.

    The output contains, for each exporter–sector–importer triplet, the value of:
    - intermediate exports,
    - final-goods exports,
    - total exports (intermediate + final).

    Parameters
    ----------
    dic : dict
        MRIO dictionary with at least:
        - "df"  : pandas.DataFrame, MRIO table (rows = CS, columns = CS + CFD [+ OUT]).
        - "C"   : int, number of countries.
        - "S"   : int, number of sectors per country.
        - "FD"  : int, number of final-demand categories per country.
        - "CS"  : int, C × S.
        - "CFD" : int, C × FD.

    Returns
    -------
    df_t : pandas.DataFrame
        Long-format DataFrame with columns:
        - "exporter" : str, ISO3 code of exporting country (i).
        - "sector"   : str, sector index (k) as string.
        - "importer" : str, ISO3 code of importing country (n).
        - "interm"   : float, exports of intermediate goods from (i,k) to n.
        - "final"    : float, exports of final goods from (i,k) to n.
        - "trade"    : float, total exports = interm + final.
    """

    # Unpack MRIO components
    df, C, S, FD, CS, CFD = (
        dic["df"],
        dic["C"],
        dic["S"],
        dic["FD"],
        dic["CS"],
        dic["CFD"],
    )


    # ============================
    # 1. INTERMEDIATE GOODS (Z)
    # ============================
    Z = df.iloc[:CS, :CS]

    # exporter-sector (rows)
    i = Z.index.str[:3]
    k = Z.index.str[4:]

    # importer (columns)
    n = Z.columns.str[:3]

    # sum over destination sectors j FIRST (huge speedup)
    # Z_agg = (Z.groupby(n, axis=1).sum().groupby([i, k]).sum())
    Z_agg = (Z.T.groupby(n).sum().T.groupby([i, k]).sum())

    # reshape to long
    Z_t = (Z_agg.stack().rename("interm").reset_index().rename(columns={"level_2": "importer"}))


    # ============================
    # 2. FINAL GOODS (Yfd)
    # ============================
    Y = df.iloc[:CS, CS:CS + CFD]

    i = Y.index.str[:3]
    k = Y.index.str[4:]
    n = Y.columns.str[:3]

    # Y_agg = (Y.groupby(n, axis=1).sum().groupby([i, k]).sum())
    Y_agg = (Y.T.groupby(n).sum().T.groupby([i, k]).sum())

    Yfd_t = (Y_agg.stack().rename("final").reset_index().rename(columns={"level_2": "importer"}))



    
    # ------------------------------------------------------------------
    # 3. Combine intermediate and final exports
    # ------------------------------------------------------------------
    df_t = pd.merge(Z_t, Yfd_t[["final"]], left_index=True, right_index=True)
    # df_t.columns = ["interm", "final"]

    # Ensure numeric types
    df_t["interm"] = pd.to_numeric(df_t["interm"])
    df_t["final"] = pd.to_numeric(df_t["final"])

    # Total exports = intermediate + final
    df_t["trade"] = df_t["interm"] + df_t["final"]

    # Reset index and rename columns for gravity-ready format
    # df_t = df_t.reset_index()
    df_t.columns = ["exporter", "sector", "importer", "interm", "final", "trade"]

    print("Gravity Object Done!")
    return df_t



def obj_Grav_panel(dicc):
    """
    Build a multi-year panel of bilateral trade flows for gravity estimation.

    This function iterates over a dictionary of MRIO dictionaries (one per year),
    applies `obj_Grav` to each of them, and stacks the resulting cross-sections
    into a single panel DataFrame with a year identifier.

    Parameters
    ----------
    dicc : dict
        Dictionary of the form:
            { year_1: dic_1, year_2: dic_2, ... }
        where each `dic_t` is an MRIO dictionary suitable for `obj_Grav`
        (i.e. has keys "df", "C", "S", "FD", "CS", "CFD").

    Returns
    -------
    panel_df : pandas.DataFrame
        Long-format panel with columns:
        - "exporter" : str, ISO3 code of exporting country.
        - "sector"   : str, sector index.
        - "importer" : str, ISO3 code of importing country.
        - "interm"   : float, intermediate exports.
        - "final"    : float, final-goods exports.
        - "trade"    : float, total exports.
        - "year"     : int or str, year identifier.
    """

    panel_data = []  # list to collect data for each year

    for year, dic in dicc.items():
        print(year)
        # Generate the bilateral trade DataFrame for this year
        df_t = obj_Grav(dic)

        # Add year identifier
        df_t["year"] = year

        # Append to list
        panel_data.append(df_t)

    # Stack all years into a single panel DataFrame
    panel_df = pd.concat(panel_data, ignore_index=True)

    print("Gravity Panel Object Done!")
    
    return panel_df


# %%


# %% [markdown]
# # 3-A INPUT - OUTPUT 
# Matrices I-O
# 
# <details>
# <summary><strong>Matrix name and description</strong> (ver códigos)</summary>
# 
# | Matrix   | Descripción                                          | Dimensions       |
# |----------|------------------------------------------------------|------------------|
# | Z        | Intermediate inputs                                  | C*S x C*S        |
# | Zd       | Domestic intermediate inputs                         | C*S x C*S        |
# | Zm       | Foreign intermediate inputs                          | C*S x C*S        |
# | A        | Coefficient matrix                                   | C*S x C*S        |
# | Ad       | Domestic coefficient matrix                          | C*S x C*S        |
# | Am       | Foreign coefficient matrix                           | C*S x C*S        |
# | B        | Global Leontief inverse                              | C*S x C*S        |
# | Bd       | Domestic global Leontief inverse                     | C*S x C*S        |
# | Bm       | Foreign global Leontief inverse                      | C*S x C*S        |
# | Ld       | Local Leontief inverse matrices                      | C*S x C*S        |
# | Yfd      | Final demand, with components                        | C*S x C*FD       |
# | Y        | Final demand                                         | C*S x C          |
# | Yd       | Domestic final demand                                | C*S x C          |
# | Ym       | Foreign final demand                                 | C*S x C          |
# | VA       | Value added                                          | C*S x 1          |
# | V        | Value added coefficients                             | C*S x 1          |
# | W        | Diagonalized VA coefficients (V-hat)                 | C*S x C*S        |
# | X        | Production                                           | C*S x 1          |
# | EXGR     | Gross bilateral exports                              | C*S x C          |
# | E        | Diagonalized total gross exports (E-hat)             | C*S x C*S        |
# 
# | Variable     | Descripción                                                        |
# |--------------|--------------------------------------------------------------------|
# | Vt (TC)      | Total VA content                                                   |
# | Vd (DC)      | Domestic VA content                                                |
# | Vf (FC)      | Foreign VA content                                                 |
# | Vt_edc (TVA) | Total VA (excluding double counting)                               |
# | Vd_edc (DVA) | Domestic VA (excluding double counting)                            |
# | Vf_edc (FVA) | Foreign VA (excluding double counting)                             |
# | EXGR         | Total gross exports                                                |
# | EXGRY        | Total exports, in terms of absorption                              |
# | EXGRY_INT    | Exports of intermediates, in terms of absorption                    |
# | EXGRY_FIN    | Exports of final products, in terms of absorption                   |
# 
# </details>
# 

# %%


# %% [markdown]
# ## WWZ - Wang–Wei–Zhu (2018)

# %%
# No funciona solo obtengo unos cuantos componentes
def WWZ(wio, agg: str = ""):
    """
    Compute the Wang–Wei–Zhu (2018) value-added trade decomposition.

    Parameters
    ----------
    wio : dict
        Input–output object as returned by `obj_IO`, with at least:
        - wio["Z"], wio["Zd"], wio["Zm"] : intermediate input matrices
        - wio["A"], wio["Ad"], wio["Am"] : technical coefficients (total / domestic / foreign)
        - wio["B"], wio["Bd"], wio["Bm"] : Leontief inverse (total / domestic / foreign)
        - wio["Y"], wio["Yd"], wio["Ym"] : final demand (total / domestic / foreign)
        - wio["L"]                       : local (domestic) Leontief inverse
        - wio["Yfd"]                     : full final demand by country–component
        - wio["VA"], wio["V"], wio["W"]  : value added (levels, coefficients, diagonal)
        - wio["X"], wio["EXGR"], wio["E"]: gross output and exports
        - wio["dims"]                    : dict with C, S, FD, CS, CFD
        - wio["names"]                   : dict with country and sector names



    agg : {"", "ORI", "DES", "SEC", "ORI-SEC"}, default ""
        Optional aggregation level for the decomposition results.

        If `agg == ""` (default):
            - The function returns the full bilateral WWZ decomposition at
              the (origin country–sector, destination country) level.
            - Index format:
                "<origin_country>_<origin_sector>_<destination_country>"

        If `agg == "ORI"`:
            - Aggregates all components by country of origin.
            - The index becomes 3-letter ISO origin country codes.
            - Each row gives the total WWZ decomposition over all sectors
              and all destinations for that origin.

        If `agg == "DES"`:
            - Aggregates all components by country of destination.
            - The index becomes 3-letter ISO destination country codes.
            - Each row gives the total decomposition over all origin
              countries and sectors for that destination.

        If `agg == "SEC"`:
            - Aggregates all components by sector of origin (across all
              countries and all destinations).
            - The index becomes sector identifiers (the middle token
              between the two underscores in the original index).

        If `agg == "ORI-SEC"`:
            - Aggregates by origin country–sector pair (collapsing the
              destination dimension).
            - The index becomes "<origin_country>_<origin_sector>", and
              each row gives the total decomposition over all destinations.


    Returns
    -------
    WWZ_df : pandas.DataFrame
        Long-format WWZ decomposition with 16 components for each
        (origin country–sector, destination country) combination.

        Index:
            "<origin_country>_<origin_sector>_<destination_country>"
            (built from `cs_names` × `c_names`)

        Columns:
            [
                "DVA_FIN",   # 1  Domestic VA in final goods exports
                "DVA_INT",   # 2  Domestic VA in intermediates absorbed by direct importer
                "DVA_INTrex1",# 3 Domestic VA in intermediates -> 3rd country final use
                "DVA_INTrex2",# 4 Domestic VA in intermediates -> 3rd country final exports
                "DVA_INTrex3",# 5 Domestic VA in intermediates -> 3rd country intermediates
                "RDV_FIN1",  # 6  Returned DVA in final imports (direct importer)
                "RDV_FIN2",  # 7  Returned DVA in final imports (via third countries)
                "RDV_INT",   # 8  Returned DVA in intermediate imports used domestically
                "DDC_FIN",   # 9  Double-counted DVA in final exports
                "DDC_INT",   # 10 Double-counted DVA in intermediate exports
                "MVA_FIN",   # 11 Foreign (imported) VA in final goods exports (direct)
                "OVA_FIN",   # 12 Other countries' VA in final goods exports (via others)
                "MVA_INT",   # 13 Foreign VA in intermediate exports (direct)
                "OVA_INT",   # 14 Other countries' VA in intermediate exports
                "MDC",       # 15 Multilateral double-counting
                "ODC"        # 16 Other double-counting
            ]

    Notes
    -----
    - Term numbering follows Table A2 in Wang, Wei and Zhu (2018).
    - Some notation follows Quast & Stolzenburg (2015, decompr package).
    """
    # ------------------------------------------------------------------
    # 0. Checks
    # ------------------------------------------------------------------
    required_keys = ["Z","Zd","Zm","A","Ad","Am","B","Bd","Bm","Y","Yd","Ym","L","Yfd","VA","V","W","X","EXGR","E","dims","names"]
    for k in required_keys:
        if k not in wio:
            raise KeyError(f"Missing key '{k}' in wio object.")
            
    if wio["dims"]["CS"] != wio["dims"]["C"] * wio["dims"]["S"]:
        raise ValueError(f"Inconsistent dimensions: CS={wio["dims"]["CS"]}, but C*S={wio["dims"]["C"]*wio["dims"]["S"]}.")
        
    # ------------------------------------------------------------------
    # 1. Unpack matrices and dimensions from the wio object
    # ------------------------------------------------------------------
    Z, Zd, Zm, A, Ad, Am, B, Bd, Bm, Y, Yd, Ym, L, Yfd, VA, V, W, X, EXGR, E = (
        wio["Z"], wio["Zd"], wio["Zm"], wio["A"], wio["Ad"], wio["Am"],
        wio["B"], wio["Bd"], wio["Bm"], wio["Y"], wio["Yd"], wio["Ym"],
        wio["L"], wio["Yfd"], wio["VA"], wio["V"], wio["W"], wio["X"],
        wio["EXGR"], wio["E"]
    )

    C, S, FD, CS, CFD = (
        wio["dims"]["C"], wio["dims"]["S"], wio["dims"]["FD"],
        wio["dims"]["CS"], wio["dims"]["CFD"]
    )

    c_names, s_names, fd_names, cs_names, cfd_names = (
        wio["names"]["c_names"], wio["names"]["s_names"],
        wio["names"]["fd_names"], wio["names"]["cs_names"],
        wio["names"]["cfd_names"]
    )

    if Yfd.shape[1] != C:
        print("FD aggregation")
        Yfd = Yfd.reshape(X.shape[0], C, FD).sum(axis=2)

    # ------------------------------------------------------------------
    # 2. Country–sector block masks (domestic vs foreign)
    # ------------------------------------------------------------------
    block_diag1_CSxCS = np.kron(np.identity(C), np.ones((S, S)))        # domestic CS×CS
    block_diag0_CSxCS = np.ones((C * S, C * S)) - block_diag1_CSxCS     # foreign CS×CS

    block_diag1_CSxC = np.kron(np.identity(C), np.ones((S, 1)))         # domestic CS×C
    block_diag0_CSxC = np.ones((S * C, C)) - block_diag1_CSxC           # foreign CS×C

    block_diag1_CSxCSC = np.concatenate([block_diag1_CSxCS, block_diag1_CSxC], axis=1)
    block_diag0_CSxCSC = np.ones((S * C, S * C + C)) - block_diag1_CSxCSC

    # ------------------------------------------------------------------
    # 3. Prepare container for WWZ results
    #    Dimensions: (origin CS, destination C, 16 components)
    # ------------------------------------------------------------------
    WWZ_array = np.zeros((C * S, C, 16))

    # ------------------------------------------------------------------
    # Term 1: DVA_FIN
    # Domestic value added embodied in final goods exports
    # ------------------------------------------------------------------
    Bd_V = Bd * V  # domestic Leontief inverse weighted by VA coefficients

#  vectorized JdL 2/12/2025 sustituye bucle
    col_sums = Bd_V.sum(axis=0)          # CS-long vector
    WWZ_array[:, :, 0] = col_sums[:, None] * Ym
    
    # for i in range(C):
    #     # Ym_i: replicate Ym[:, i] across CS columns (same importer i)
    #     Ym_i = np.outer(Ym[:, i], np.ones(C * S)).T
    #     # Row-wise sums over CS give DVA in final exports to importer i
    #     WWZ_array[:, i, 0] = (Bd_V * Ym_i).sum(axis=0)

    # ------------------------------------------------------------------
    # Term 2: DVA_INT
    # DVA in intermediary exports absorbed by direct importer
    # ------------------------------------------------------------------
    V_L = V * L
    V_LSum0 = V_L.sum(axis=0)               # row-aggregated domestic link
    Am_Bd_Yd = Am.dot(Bd).dot(Yd)           # foreign A × domestic B × domestic Y

    # Vectorized across all importers
    WWZ_array[:, :, 1] = V_LSum0[:, np.newaxis] * Am_Bd_Yd

    # ------------------------------------------------------------------
    # Term 3: DVA_INTrex1
    # DVA in intermediates → direct importer → 3rd countries’ domestic final use
    # ------------------------------------------------------------------
    z1 = Yd.sum(axis=1)[:, np.newaxis] @ (np.ones((1, C * S)))
    z1 = z1 * block_diag0_CSxCS                 # only cross-country flows
    z2 = Bm @ z1
    z2 = z2 * block_diag0_CSxCS                 # again, cross-country only
    z3 = Am * (z2.T)

    # Sum within each destination country bloc (S sectors)
    z3_summed = np.array([z3[:, i * S:(i + 1) * S].sum(axis=1) for i in range(C)]).T
    WWZ_array[:, :, 2] = V_LSum0[:, np.newaxis] * z3_summed

    # ------------------------------------------------------------------
    # Term 4: DVA_INTrex2
    # DVA in intermediates → direct importer → final exports to 3rd countries
    # ------------------------------------------------------------------
    z = np.zeros((C * S, C * S))
    z1 = Ym.sum(axis=1)

    for i in range(C):
        # All foreign final exports except those going to importer i
        z[:, i * S:(i + 1) * S] = (z1 - Ym[:, i])[:, np.newaxis] @ np.ones((1, S))
        # Remove domestic block
        z[i * S:(i + 1) * S, i * S:(i + 1) * S] = 0

    z2 = Am * (Bd.dot(z).T)
    for i in range(C):
        WWZ_array[:, i, 3] = V_LSum0 * z2[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # Term 5: DVA_INTrex3
    # DVA in intermediates → direct importer → intermediates to 3rd countries
    # ------------------------------------------------------------------
    z1 = Bm.dot(z).T
    z1 = z1 * block_diag0_CSxCS
    z2 = Am * z1

    for i in range(C):
        WWZ_array[:, i, 4] = V_LSum0 * z2[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # CATEGORY 4: RDV (Returned Domestic Value Added)
    # Term 6: RDV_FIN1
    # Returned DVA in final goods imports from the direct importer
    # ------------------------------------------------------------------
    z = np.zeros((C * S, C * S))
    for i in range(C):
        z[:, i * S:(i + 1) * S] = Ym[:, i][:, np.newaxis] @ np.ones((1, S))

    z1 = Am * (Bd.dot(z).T)
    for i in range(C):
        WWZ_array[:, i, 5] = V_LSum0 * z1[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # Term 7: RDV_FIN2
    # Returned DVA in final imports via third countries
    # ------------------------------------------------------------------
    z1 = Bm.dot(z)
    z1 = z1 * block_diag0_CSxCS
    z2 = Am * (z1.T)

    for i in range(C):
        WWZ_array[:, i, 6] = V_LSum0 * z2[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # Term 8: RDV_INT
    # Returned DVA in intermediate imports used to produce final goods consumed at home
    # ------------------------------------------------------------------
    z = np.zeros((C * S, C * S))
    for i in range(C):
        z[:, i * S:(i + 1) * S] = Yd[:, i][:, np.newaxis] @ np.ones((1, S))

    z1 = Am * (Bm.dot(z).T)
    for i in range(C):
        WWZ_array[:, i, 7] = V_LSum0 * z1[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # CATEGORY 5: DDC (Double-counted domestic VA)
    # Term 9: DDC_FIN
    # Double-counted DVA used to produce final goods exports
    # ------------------------------------------------------------------
    z = np.zeros((C * S, C * S))
    for i in range(C):
        block_sum = Ym[i * S:(i + 1) * S, :].sum(axis=1)
        z[i * S:(i + 1) * S, i * S:(i + 1) * S] = block_sum[:, np.newaxis] @ np.ones((1, S))

    z1 = Am * (Bm.dot(z)).T
    for i in range(C):
        WWZ_array[:, i, 8] = V_LSum0 * z1[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # Term 10: DDC_INT
    # Double-counted DVA used to produce intermediate exports
    # ------------------------------------------------------------------
    Am_X = Am * X
    V_Bd_V_LSum0 = ((V * Bd) - V_L).sum(axis=0)

    for i in range(C):
        WWZ_array[:, i, 9] = V_Bd_V_LSum0 * Am_X[:, i * S:(i + 1) * S].sum(axis=1)

    # ------------------------------------------------------------------
    # CATEGORY 6 & 7: Foreign VA in exports (MVA/OVA) and double counting
    # ------------------------------------------------------------------
    VrBrs = V * Bm

    # Terms 11 (MVA_FIN) and 12 (OVA_FIN)
    for i in range(C):
        Ym_i = Ym[:, i][:, np.newaxis] @ np.ones((1, C * S))
        z = VrBrs * Ym_i.T

        # Mask for separating own vs other rows
        zmask = np.ones_like(z, dtype=bool)
        zmask[i * S:(i + 1) * S, :] = 0

        # Direct importer rows
        WWZ_array[:, i, 10] = z[i * S:(i + 1) * S, :].sum(axis=0)
        # Other countries' rows
        WWZ_array[:, i, 11] = z[zmask].reshape((C * S - S, C * S)).sum(axis=0)

    # Terms 13 (MVA_INT) and 14 (OVA_INT)
    Am_L = Am.dot(L)
    for i in range(C):
        # Yd_i = Yd[:, i][:, np.newaxis] @ np.ones((1, C * S))
        Yd_i = Yd[:, i][:, np.newaxis].dot(np.ones((1, C * S))).T
        # zz = (Am_L * Yd_i.T).sum(axis=1)
        zz = (Am_L * Yd_i).sum(axis=1)
        # zz_i = zz[:, np.newaxis] @ np.ones((1, C * S))
        zz_i = zz[:, np.newaxis].dot(np.ones((1, C * S))).T
        
        z = VrBrs * zz_i

        zmask = np.ones_like(z, dtype=bool)
        zmask[i * S:(i + 1) * S, :] = 0

        WWZ_array[:, i, 12] = z[i * S:(i + 1) * S, :].sum(axis=0)
        WWZ_array[:, i, 13] = z[zmask].reshape((C * S - S, C * S)).sum(axis=0)

    # Terms 15 (MDC) and 16 (ODC): multilateral and other double-counting
    EE = (np.hstack((Z, Yfd)) * block_diag0_CSxCSC).sum(axis=1).reshape(-1, 1)

    for i in range(C):
        # Er = np.zeros((C * S, 1))
        # # Total cross-border exports from origin bloc i
        # Er[i * S:(i + 1) * S, 0] = EE[i * S:(i + 1) * S, 0]
        # Er_i = Er @ np.ones((1, C * S))
        # # zz = (Am_L * Er_i.T).sum(axis=1)
        # zz = (Am_L * Er_i).sum(axis=1)
        # # zz_i = zz[:, np.newaxis] @ np.ones((1, C * S))
        # zz_i = zz[:, np.newaxis].dot(np.ones((1, C * S))).T
        
        # z = VrBrs * zz_i

        # zmask = np.ones_like(z, dtype=bool)
        # zmask[i * S:(i + 1) * S, :] = 0

        # WWZ_array[:, i, 14] = z[i * S:(i + 1) * S, :].sum(axis=0)
        # WWZ_array[:, i, 15] = z[zmask].reshape((C * S - S, C * S)).sum(axis=0)


        Er = np.zeros((C*S,1))
        Er[i*S:(i+1)*S, 0] = EE.sum(axis=1).reshape(-1, 1)[i*S:(i+1)*S, 0]
        Er_i = Er.dot( np.ones((1,C*S)) ).T
        zz = (Am_L * Er_i).sum(axis=1)
        zz_i = zz[:, np.newaxis].dot( np.ones((1,C*S)) ).T
        z = VrBrs * zz_i
        zmask = np.array(np.ones_like(z), dtype=bool)
        zmask[ i*S:(i+1)*S, : ] = 0
        # WWZ[:, i, 14] = z[ i*S:(i+1)*S, : ].sum(axis=0)             # 15 MDC: J rows selected and summed
        # WWZ[:, i, 15] = (z[zmask].reshape((C*S-S,C*S)) ).sum(axis=0)  # 16 ODC: all except J rows selected and summed
        WWZ_array[:, i, 14] = z[i * S:(i + 1) * S, :].sum(axis=0)
        WWZ_array[:, i, 15] = z[zmask].reshape((C * S - S, C * S)).sum(axis=0)

    
    # ------------------------------------------------------------------
    # 4. Build labeled DataFrame
    # ------------------------------------------------------------------
    WWZ_columns = [
        "DVA_FIN",   "DVA_INT",   "DVA_INTrex1", "DVA_INTrex2",
        "DVA_INTrex3","RDV_FIN1",  "RDV_FIN2",    "RDV_INT",
        "DDC_FIN",   "DDC_INT",   "MVA_FIN",     "OVA_FIN",
        "MVA_INT",   "OVA_INT",   "MDC",         "ODC"
    ]

    # Index: origin country–sector × destination country
    combinations = [f"{cs}_{c}" for cs, c in itertools.product(cs_names, c_names)]

    WWZ_df = pd.DataFrame(
        WWZ_array.reshape(-1, 16),
        index=combinations,
        columns=WWZ_columns
    )



    # ------------------------------------------------------------------
    # 5. Optional aggregation by origin/destination/sector
    # ------------------------------------------------------------------
    # We add a helper "Group" column based on the original index and then
    # group by that tag. When aggregation is requested, the index of the
    # returned DataFrame becomes the group label.
    if agg == "ORI":
        # Group by country of origin (first 3 characters of the index)
        print("Country of origin")
        WWZ_df["Group"] = WWZ_df.index.str[:3]
        WWZ_df = WWZ_df.groupby(WWZ_df["Group"]).sum()
    elif agg == "DES":
        # Group by country of destination (last 3 characters of the index)
        print("Country of destination")
        WWZ_df["Group"] = WWZ_df.index.str[-3:]
        WWZ_df = WWZ_df.groupby(WWZ_df["Group"]).sum()

    elif agg == "ORI-DES":
        # Group by origin–destination pair (drop sector)
        print("Country of origin / Country of destination")
        WWZ_df["Group"] = WWZ_df.index.astype(str).str.split("_").str[0] + "_" + WWZ_df.index.astype(str).str.split("_").str[-1]
        WWZ_df = WWZ_df.groupby(WWZ_df["Group"]).sum()
        
    elif agg == "SEC":
        # Group by sector of origin:
        # remove first and last tokens (country origin and destination),
        # keep only the middle token (sector)
        print("Sector of origin")
        WWZ_df["Group"] = WWZ_df.index.astype(str).str.replace(r'^[^_]*_|_[^_]*$', '', regex=True )
        WWZ_df = WWZ_df.groupby(WWZ_df["Group"]).sum()
    elif agg == "ORI-SEC":
        # Group by origin country–sector pair (drop destination code)
        print("Country/Sector of origin")
        WWZ_df["Group"] = WWZ_df.index.astype(str).str.replace(r'_[^_]*$', '', regex=True)
        WWZ_df = WWZ_df.groupby(WWZ_df["Group"]).sum()

    print("WWZ Done!")
    return WWZ_df


# %%


# %% [markdown]
# ## KWW

# %%
def KWW(io, agg ="", shares: bool = False) -> pd.DataFrame:
    """
    Aggregate the detailed WWZ decomposition into KWW-style components.

    This function takes the full Wang–Wei–Zhu (WWZ) decomposition (as
    returned by `WWZ(io)`) and groups its 16 detailed components into
    a smaller set of economically meaningful categories in the
    Koopman–Wang–Wei (KWW) style.

    Parameters
    ----------
    io : dict
        World input–output object to be passed to `WWZ(io)`. It must be
        compatible with your `WWZ` function (i.e. `WWZ(io)` returns a
        DataFrame with the 16 WWZ components as columns).
    shares : bool, default False
        - If False: return levels (same units as the WWZ decomposition).
        - If True:  return shares (percent) of each KWW component in
                    total gross exports for each origin–destination
                    combination. In that case, the `Tot` column will
                    equal 100 for every row.

    Returns
    -------
    KWW_c : pandas.DataFrame
        DataFrame with the same index as `WWZ(io)` (typically
        origin-country-sector × destination-country) and columns:

        - "DVA_FIN"   : domestic VA in final goods exports
        - "DVA_INT"   : domestic VA in intermediate exports absorbed
                        by the direct importer
        - "DVA_INTrex": domestic VA in intermediate exports that is
                        re-exported (third-country use)
        - "RDV_FIN"   : returned domestic VA in final goods
        - "RDV_INT"   : returned domestic VA in intermediates
        - "DDC"       : double-counted domestic content
        - "FVA_FIN"   : foreign VA in final goods exports
        - "FVA_INT"   : foreign VA in intermediate exports
        - "FDC"       : foreign double-counting
        - "Tot"       : total (sum of all previous KWW components);
                        if `shares=True`, Tot = 100 for every row.
    """

    # 1) Compute the detailed WWZ decomposition (16 components)
    WWZ_c = WWZ(io,agg)  # assumes WWZ(io) → DataFrame (rows = flows, cols = WWZ terms)

    # 2) Mapping from WWZ components (columns) to KWW-style aggregates
    #    (you can switch to the T1–T9 mapping by replacing this dict)
    mapping = {
        "DVA_FIN":    "DVA_FIN",
        "DVA_INT":    "DVA_INT",
        "DVA_INTrex1":"DVA_INT",
        "DVA_INTrex2":"DVA_INTrex",
        "DVA_INTrex3":"DVA_INTrex",
        "RDV_FIN1":   "RDV_FIN",
        "RDV_FIN2":   "RDV_FIN",
        "RDV_INT":    "RDV_INT",
        "DDC_FIN":    "DDC",
        "DDC_INT":    "DDC",
        "MVA_FIN":    "FVA_FIN",
        "OVA_FIN":    "FVA_FIN",
        "MVA_INT":    "FVA_INT",
        "OVA_INT":    "FVA_INT",
        "MDC":        "FDC",
        "ODC":        "FDC",
    }

    # 3) Group WWZ columns by the mapping and sum them → KWW components
    #    We transpose to group by columns, then transpose back.
    KWW_c = WWZ_c.T.groupby(WWZ_c.columns.map(mapping)).sum().T

    # 4) Add total (sum of all KWW components per flow)
    KWW_c["Tot"] = KWW_c.sum(axis=1)

    # 5) Optionally convert to percentage shares
    if shares:
        # Divide each column by the sum of *all KWW components except Tot*
        # so that Tot becomes 100 for every row.
        denom = KWW_c.iloc[:, :-1].sum(axis=1)
        KWW_c = KWW_c.div(denom, axis=0) * 100

    KWW_c = KWW_c[['DVA_FIN', 'DVA_INT', 'DVA_INTrex', 'RDV_FIN', 'RDV_INT', 'DDC', 'FVA_FIN', 'FVA_INT', 'FDC', 'Tot']]

    print("KWW Done!")
    
    return KWW_c






# %%


# %% [markdown]
# ## Borin & Mancini 2023

# %%

def BM_2023(wio: dict, shares: bool = False, agg: str | None = None) -> pd.DataFrame:
    """
    Borin & Mancini–style value-added export decomposition (strict W–B–E version).

    Computes Domestic Value Added (DVA), Foreign Value Added (FVA) and total
    value-added exports (VAX = DVA + FVA) using:

        M = W @ B @ E

    Strict input requirements:
      - B : (CS×CS)
      - W : (CS×CS) diagonal, OR V : (CS,) vector (converted to diag)
      - E : (CS×CS) diagonal, OR (CS,) vector (converted to diag)

    Parameters
    ----------
    wio : dict
        Must contain:
          - "B"
          - "W" (diagonal) or "V" (vector)
          - "E" (diagonal) or vector
          - "dims": {"C","S","CS"}
          - "names": {"cs_names"}

    shares : bool, default False
        If True, returns DVA and FVA as % shares of (DVA+FVA) per row.

    agg : {None, "ORI-SEC", "ORI", "SEC"}, default None
        Aggregation level.

    Returns
    -------
    pandas.DataFrame with columns ["DVA","FVA","VAX"].
    """

    # ---- dims / names ----
    C = int(wio["dims"]["C"])
    S = int(wio["dims"]["S"])
    CS = int(wio["dims"]["CS"])
    if CS != C * S:
        raise ValueError(f"Inconsistent dimensions: CS={CS}, but C*S={C*S}.")

    cs_names = np.asarray(wio["names"]["cs_names"], dtype=str)

    # ---- B ----
    B = np.asarray(wio["B"])
    if B.shape != (CS, CS):
        raise ValueError("wio['B'] must be a (CS×CS) matrix.")

    # ---- W (or V) ----
    if "W" in wio:
        W = np.asarray(wio["W"])
        if W.shape != (CS, CS):
            raise ValueError("wio['W'] must be a (CS×CS) matrix.")
        if not np.allclose(W, np.diag(np.diag(W))):
            raise ValueError("wio['W'] must be diagonal (CS×CS).")
    elif "V" in wio:
        v = np.asarray(wio["V"]).reshape(-1)
        if v.shape[0] != CS:
            raise ValueError("wio['V'] must have length CS.")
        W = np.diag(v)
    else:
        raise ValueError("wio must contain 'W' (diag CS×CS) or 'V' (length CS).")

    # ---- E (strict) ----
    E_raw = np.asarray(wio["E"])
    if E_raw.ndim == 1:
        if E_raw.shape[0] != CS:
            raise ValueError("If wio['E'] is a vector, its length must be CS.")
        E = np.diag(E_raw)
    elif E_raw.ndim == 2:
        if E_raw.shape != (CS, CS):
            raise ValueError("If wio['E'] is a matrix, it must be (CS×CS).")
        if not np.allclose(E_raw, np.diag(np.diag(E_raw))):
            raise ValueError("wio['E'] must be diagonal (CS×CS).")
        E = E_raw
    else:
        raise ValueError("wio['E'] must be a 1D vector or a 2D matrix.")

    # ---- core ----
    M = (W @ B) @ E  # (CS×CS)

    origin_country = np.array([name.split("_", 1)[0] for name in cs_names])
    eq_countries = origin_country[:, None] == origin_country[None, :]

    DVA_cs = (M * eq_countries).sum(axis=0)
    FVA_cs = (M * (~eq_countries)).sum(axis=0)
    VAX_cs = M.sum(axis=0)

    agg_norm = None if agg is None else str(agg).upper()

    if agg_norm in (None, "ORI-SEC"):
        DVA, FVA, VAX = DVA_cs, FVA_cs, VAX_cs
        index = cs_names

    elif agg_norm == "ORI":
        tmp = pd.DataFrame({"exporter": origin_country, "DVA": DVA_cs, "FVA": FVA_cs, "VAX": VAX_cs})
        g = tmp.groupby("exporter", as_index=True).sum()
        DVA, FVA, VAX = g["DVA"].to_numpy(), g["FVA"].to_numpy(), g["VAX"].to_numpy()
        index = g.index.to_numpy()

    elif agg_norm == "SEC":
        sector_code = np.array([name.split("_", 1)[1] for name in cs_names])
        tmp = pd.DataFrame({"sector": sector_code, "DVA": DVA_cs, "FVA": FVA_cs, "VAX": VAX_cs})
        g = tmp.groupby("sector", as_index=True).sum()
        DVA, FVA, VAX = g["DVA"].to_numpy(), g["FVA"].to_numpy(), g["VAX"].to_numpy()
        index = g.index.to_numpy()

    else:
        raise ValueError("agg must be one of {None, 'ORI-SEC', 'ORI', 'SEC'}.")

    df = pd.DataFrame({"DVA": DVA, "FVA": FVA, "VAX": VAX}, index=index)
    df.index.name = None

    if shares:
        total_va = df[["DVA", "FVA"]].sum(axis=1).replace(0, np.nan)
        df[["DVA", "FVA"]] = df[["DVA", "FVA"]].div(total_va, axis=0).mul(100.0)

    print("BM Done!")
    
    return df


# %%


# %% [markdown]
# ## Borin & Mancini 2025 Trade

# %%
def BM_2025_trade(io, selector: str = "all_all", measures: bool = True) -> pd.DataFrame:
    """
    BM2025 tripartite GVC trade decomposition (todo integrado, sin dependencias externas).

    Parameters
    ----------
    io : dict
        Diccionario estilo bm_io con al menos:
          - A (GN×GN), Y (GN×G), Z (GN×GN), v (GN,)
          - countries (len G), sectors (len N), G, N, GN
          - opcional: country_codes (para permitir pasar "CHN", "USA", etc. como input)
    selector : str, default "all_all"
        mode_granularity:
          mode ∈ {"bilateral","total","all"}
          granularity ∈ {"agg","sectoral","all"}

        Ejemplos:
          - "bilateral_agg"      -> pares (s,r) agregados (sector="ALL")
          - "bilateral_sectoral" -> pares (s,r) por sector del exportador
          - "total_agg"          -> totales por exportador (importer=NaN, sector="ALL")
          - "total_sectoral"     -> totales por exportador y sector (importer=NaN)
          - "all_all"            -> TODO (bilateral + total) y (agg + sectoral)
    measures : bool, default True
        Si True, calcula shares y forward sobre TOTALES (exporter, sector) y los pega a todas las filas.

    Returns
    -------
    pd.DataFrame
        Siempre incluye ["mode","exporter","importer","sector", ...]
    """

    # -----------------
    # Parse selector
    # -----------------
    selector = str(selector).lower().strip()
    valid_mode = {"bilateral", "total", "all"}
    valid_gran = {"agg", "sectoral", "all"}

    if "_" not in selector:
        raise ValueError("selector debe ser 'mode_granularity', p.ej. 'all_all'.")

    mode_sel, gran_sel = selector.split("_", 1)
    if mode_sel not in valid_mode:
        raise ValueError(f"mode inválido: {mode_sel}. Usa {sorted(valid_mode)}")
    if gran_sel not in valid_gran:
        raise ValueError(f"granularity inválida: {gran_sel}. Usa {sorted(valid_gran)}")

    want_bilateral = mode_sel in {"bilateral", "all"}
    want_total     = mode_sel in {"total", "all"}
    want_agg       = gran_sel in {"agg", "all"}
    want_sectoral  = gran_sel in {"sectoral", "all"}

    # -----------------
    # Core arrays
    # -----------------
    # A = np.asarray(io["A"], dtype=float)
    # Y = np.asarray(io["Y"], dtype=float)
    # Z = np.asarray(io["Z"], dtype=float)
    # v = np.asarray(io["v"], dtype=float).reshape(-1)

    # G  = int(io["G"])
    # N  = int(io["N"])
    # GN = int(io["GN"])

    # countries = list(io.get("countries", [f"C{i}" for i in range(1, G + 1)]))
    # sectors   = list(io.get("sectors",   [f"S{i}" for i in range(1, N + 1)]))




    Z = np.asarray(io["Z"].T, dtype=float)#nueva
    Y = np.asarray(io["Y"], dtype=float)
    VA = np.asarray(io["VA"], dtype=float)#nueva
    X = np.asarray(io["X"], dtype=float)#nueva
    countries = list(io["names"]["c_names"])
    sectors = list(io["names"]["s_names"])
    A = np.asarray(io["A"], dtype=float)
    B = np.asarray(io["B"], dtype=float)
    v = np.asarray(io["V"], dtype=float)
    G = int(io["dims"]["C"])
    N = int(io["dims"]["S"])
    GN = int(io["dims"]["CS"])

    
    # -----------------
    # Helpers internos
    # -----------------
    def country_id(x):
        # permite int (1..G) o string si existe country_codes
        if isinstance(x, (int, np.integer)):
            return int(x)
        cc = io.get("country_codes", None)
        if cc is None:
            raise ValueError("Para usar strings como 'CHN', necesitas io['country_codes'].")
        return int(cc[x])

    def idx_country(g: int) -> slice:
        start = (g - 1) * N
        return slice(start, start + N)

    def get_e_sr(s: int, r: int) -> np.ndarray:
        # e_sr (N,) = rowSums(Z[s,r]) + Y[s,r]
        is_ = idx_country(s)
        ir_ = idx_country(r)
        e_int = Z[is_, ir_].sum(axis=1)          # (N,)
        e_fin = Y[is_, r - 1]                   # (N,)
        return np.asarray(e_int + e_fin, dtype=float).ravel()

    def L_list_domestic() -> list:
        # L_g = (I - A_gg)^(-1) para cada país g. 0-based: L_list[g-1]
        I = np.eye(N)
        out = [None] * G
        for g in range(1, G + 1):
            ig = idx_country(g)
            A_gg = A[ig, ig]
            out[g - 1] = np.linalg.solve(I - A_gg, I)
        return out

    # -----------------
    # Precomputos BM2025
    # -----------------
    L_list = L_list_domestic()

    # imp_s (N,) = sum_{t != s} colSums(A_ts)  donde A_ts es bloque (t,s)
    import_intensity_by_s = [None] * (G + 1)  # 1-based
    for s in range(1, G + 1):
        is_ = idx_country(s)
        imp = np.zeros(N, dtype=float)
        for t in range(1, G + 1):
            if t == s:
                continue
            it = idx_country(t)
            A_ts = A[it, is_]                  # (N,N)
            imp += A_ts.sum(axis=0)            # (N,)
        import_intensity_by_s[s] = imp

    # sum_e_to_others_by_r[r] = sum_{j != r} e_rj  (N,)
    sum_e_to_others_by_r = [None] * (G + 1)
    for r in range(1, G + 1):
        sume = np.zeros(N, dtype=float)
        for j in range(1, G + 1):
            if j == r:
                continue
            sume += get_e_sr(r, j)
        sum_e_to_others_by_r[r] = sume

    # -----------------
    # Acumuladores para TOTAL
    # -----------------
    totals_agg = {
        s: {"E": 0.0, "DAVAX": 0.0, "GVC": 0.0, "GVC_PF": 0.0, "GVC_TS": 0.0, "GVC_PB": 0.0}
        for s in range(1, G + 1)
    }
    totals_sec = {
        s: {"E": np.zeros(N), "DAVAX": np.zeros(N), "GVC": np.zeros(N),
            "GVC_PF": np.zeros(N), "GVC_TS": np.zeros(N), "GVC_PB": np.zeros(N)}
        for s in range(1, G + 1)
    }

    # -----------------
    # Loop principal: bilateral (y acumula totales)
    # -----------------
    rows = []

    for s in range(1, G + 1):
        is_ = idx_country(s)
        v_s  = v[is_].ravel()
        L_ss = np.asarray(L_list[s - 1], dtype=float)
        imp_s = np.asarray(import_intensity_by_s[s], dtype=float).ravel()

        for r in range(1, G + 1):
            if r == s:
                continue

            ir_ = idx_country(r)
            L_rr = np.asarray(L_list[r - 1], dtype=float)

            e_sr = get_e_sr(s, r)                          # (N,)
            A_sr = A[is_, ir_]                              # (N,N)
            Y_sr = np.asarray(Y[is_, r - 1], dtype=float).ravel()
            Y_rr = np.asarray(Y[ir_, r - 1], dtype=float).ravel()

            # DAVAX
            term_final = Y_sr + A_sr @ (L_rr @ Y_rr)
            q_final = L_ss @ term_final

            # TS
            term_two = A_sr @ (L_rr @ sum_e_to_others_by_r[r])
            q_two = L_ss @ term_two

            DAVAX_vec = v_s * q_final
            PB_vec    = imp_s * q_final
            TS_vec    = imp_s * q_two
            GVC_vec   = e_sr - DAVAX_vec
            PF_vec    = GVC_vec - PB_vec - TS_vec

            # acumular totales
            totals_sec[s]["E"]      += e_sr
            totals_sec[s]["DAVAX"]  += DAVAX_vec
            totals_sec[s]["GVC"]    += GVC_vec
            totals_sec[s]["GVC_PF"] += PF_vec
            totals_sec[s]["GVC_TS"] += TS_vec
            totals_sec[s]["GVC_PB"] += PB_vec

            totals_agg[s]["E"]      += float(e_sr.sum())
            totals_agg[s]["DAVAX"]  += float(DAVAX_vec.sum())
            totals_agg[s]["GVC"]    += float(GVC_vec.sum())
            totals_agg[s]["GVC_PF"] += float(PF_vec.sum())
            totals_agg[s]["GVC_TS"] += float(TS_vec.sum())
            totals_agg[s]["GVC_PB"] += float(PB_vec.sum())

            # guardar bilateral
            if want_bilateral:
                exp = countries[s - 1]
                imp = countries[r - 1]

                if want_agg:
                    rows.append({
                        "mode": "bilateral",
                        "exporter": exp,
                        "importer": imp,
                        "sector": "ALL",
                        "E": float(e_sr.sum()),
                        "DAVAX": float(DAVAX_vec.sum()),
                        "GVC": float(GVC_vec.sum()),
                        "GVC_PF": float(PF_vec.sum()),
                        "GVC_TS": float(TS_vec.sum()),
                        "GVC_PB": float(PB_vec.sum()),
                    })

                if want_sectoral:
                    for i in range(N):
                        rows.append({
                            "mode": "bilateral",
                            "exporter": exp,
                            "importer": imp,
                            "sector": sectors[i],
                            "E": float(e_sr[i]),
                            "DAVAX": float(DAVAX_vec[i]),
                            "GVC": float(GVC_vec[i]),
                            "GVC_PF": float(PF_vec[i]),
                            "GVC_TS": float(TS_vec[i]),
                            "GVC_PB": float(PB_vec[i]),
                        })

    # -----------------
    # TOTAL si se pidió
    # -----------------
    if want_total:
        for s in range(1, G + 1):
            exp = countries[s - 1]

            if want_agg:
                d = totals_agg[s]
                rows.append({
                    "mode": "total",
                    "exporter": exp,
                    "importer": np.nan,
                    "sector": "ALL",
                    "E": float(d["E"]),
                    "DAVAX": float(d["DAVAX"]),
                    "GVC": float(d["GVC"]),
                    "GVC_PF": float(d["GVC_PF"]),
                    "GVC_TS": float(d["GVC_TS"]),
                    "GVC_PB": float(d["GVC_PB"]),
                })

            if want_sectoral:
                d = totals_sec[s]
                for i in range(N):
                    rows.append({
                        "mode": "total",
                        "exporter": exp,
                        "importer": np.nan,
                        "sector": sectors[i],
                        "E": float(d["E"][i]),
                        "DAVAX": float(d["DAVAX"][i]),
                        "GVC": float(d["GVC"][i]),
                        "GVC_PF": float(d["GVC_PF"][i]),
                        "GVC_TS": float(d["GVC_TS"][i]),
                        "GVC_PB": float(d["GVC_PB"][i]),
                    })

    out = pd.DataFrame(rows)

    # -----------------
    # Asegurar columnas base SIEMPRE + orden seguro
    # -----------------
    base_cols = ["mode", "exporter", "importer", "sector"]
    for c in base_cols:
        if c not in out.columns:
            out[c] = np.nan

    ordered = base_cols + [c for c in out.columns if c not in base_cols]
    out = out.reindex(columns=ordered)  # <- clave para no volver a ver KeyError

    # -----------------
    # Measures (sobre TOTALES exporter+sector)
    # -----------------
    if measures:
        meas_rows = []

        # sector="ALL"
        for s in range(1, G + 1):
            exp = countries[s - 1]
            d = totals_agg[s]
            meas_rows.append({
                "exporter": exp,
                "sector": "ALL",
                "E_s": float(d["E"]),
                "GVC_s": float(d["GVC"]),
                "GVC_PF_s": float(d["GVC_PF"]),
                "GVC_TS_s": float(d["GVC_TS"]),
                "GVC_PB_s": float(d["GVC_PB"]),
            })

        # sectoral
        for s in range(1, G + 1):
            exp = countries[s - 1]
            d = totals_sec[s]
            for i in range(N):
                meas_rows.append({
                    "exporter": exp,
                    "sector": sectors[i],
                    "E_s": float(d["E"][i]),
                    "GVC_s": float(d["GVC"][i]),
                    "GVC_PF_s": float(d["GVC_PF"][i]),
                    "GVC_TS_s": float(d["GVC_TS"][i]),
                    "GVC_PB_s": float(d["GVC_PB"][i]),
                })

        meas = pd.DataFrame(meas_rows)

        E = meas["E_s"].to_numpy(float)
        GVC = meas["GVC_s"].to_numpy(float)

        meas["share_GVC_trade"] = np.where(E != 0, meas["GVC_s"] / meas["E_s"], np.nan)
        meas["share_PF_trade"]  = np.where(GVC != 0, meas["GVC_PF_s"] / meas["GVC_s"], np.nan)
        meas["share_TS_trade"]  = np.where(GVC != 0, meas["GVC_TS_s"] / meas["GVC_s"], np.nan)
        meas["share_PB_trade"]  = np.where(GVC != 0, meas["GVC_PB_s"] / meas["GVC_s"], np.nan)
        meas["forward_trade"]   = np.where(GVC != 0, (meas["GVC_PF_s"] - meas["GVC_PB_s"]) / meas["GVC_s"], np.nan)

        out = out.merge(meas, on=["exporter", "sector"], how="left")

    return out


# %%


# %% [markdown]
# ## Borin & Mancini 2025 Output

# %%
def BM_2025_output(io, selector: str = "all_all", measures: bool = True) -> pd.DataFrame:
    """
    BM2025 — Output-based GVC decomposition (single entry point, InTrade-style).

    Parameters
    ----------
    io : dict
        IO dictionary (bm_io-like) with at least:
          - A : (GN, GN) technical coefficients
          - B : (GN, GN) global Leontief inverse (used for FVA intensity term)
          - Y : (GN, G) final demand by destination country
          - Z : (GN, GN) intermediate flows (used to build e_r*)
          - X : (GN,) gross output vector
          - v : (GN,) value-added coefficients (typically VA/X)
          - G : int, number of countries
          - N : int, number of sectors per country
          - GN: int, = G*N
          - countries : list[str], length G (optional; fallback C1..CG)
          - sectors   : list[str], length N (optional; fallback S1..SN)

    selector : str, default "all_all"
        A single selector combining (mode) and (granularity):
          mode ∈ {"total","all"}
          granularity ∈ {"agg","sectoral","all"}

        Examples
        --------
        - "total_agg"      -> one row per country (sector="ALL")
        - "total_sectoral" -> country×sector rows
        - "all_all"        -> returns BOTH agg + sectoral in one dataframe

        Note: output-based BM2025 has no bilateral dimension, so mode is kept
        for consistency with BM_2025_trade (total/all behave the same here).

    measures : bool, default True
        If True, adds participation indicators (shares and forward) computed row-wise:
          share_GVC_output = GVC_X / X
          share_PF_output  = GVC_PF_X / GVC_X
          share_TS_output  = GVC_TS_X / GVC_X
          share_PB_output  = GVC_PB_X / GVC_X
          forward_output   = (GVC_PF_X - GVC_PB_X) / GVC_X

    Returns
    -------
    pd.DataFrame
        Always includes columns: ["mode","country","sector", ...]
        where sector is "ALL" for aggregated rows.
    """

    # -----------------
    # Parse selector
    # -----------------
    selector = str(selector).lower().strip()
    valid_mode = {"total", "all"}
    valid_gran = {"agg", "sectoral", "all"}

    if "_" not in selector:
        raise ValueError("selector must be 'mode_granularity', e.g. 'all_all'.")

    mode_sel, gran_sel = selector.split("_", 1)
    if mode_sel not in valid_mode:
        raise ValueError(f"Invalid mode: {mode_sel}. Use one of {sorted(valid_mode)}")
    if gran_sel not in valid_gran:
        raise ValueError(f"Invalid granularity: {gran_sel}. Use one of {sorted(valid_gran)}")

    want_agg = gran_sel in {"agg", "all"}
    want_sectoral = gran_sel in {"sectoral", "all"}

    # -----------------
    # Core arrays
    # -----------------
    # A = np.asarray(io["A"], dtype=float)
    # B = np.asarray(io["B"], dtype=float)
    # Y = np.asarray(io["Y"], dtype=float)
    # Z = np.asarray(io["Z"], dtype=float)
    # X = np.asarray(io["X"], dtype=float).reshape(-1)
    # v = np.asarray(io["v"], dtype=float).reshape(-1)

    # G = int(io["G"])
    # N = int(io["N"])
    # GN = int(io["GN"])

    # countries = list(io.get("countries", [f"C{i}" for i in range(1, G + 1)]))
    # sectors = list(io.get("sectors", [f"S{i}" for i in range(1, N + 1)]))



    Z = np.asarray(io["Z"].T, dtype=float)#nueva
    Y = np.asarray(io["Y"], dtype=float)
    VA = np.asarray(io["VA"], dtype=float)#nueva
    X = np.asarray(io["X"], dtype=float)#nueva
    countries = list(io["names"]["c_names"])
    sectors = list(io["names"]["s_names"])
    A = np.asarray(io["A"], dtype=float)
    B = np.asarray(io["B"], dtype=float)
    v = np.asarray(io["V"], dtype=float)
    G = int(io["dims"]["C"])
    N = int(io["dims"]["S"])
    GN = int(io["dims"]["CS"])
    # -----------------
    # Helpers (internal)
    # -----------------
    def idx_country_slice(g: int) -> slice:
        start = (g - 1) * N
        return slice(start, start + N)

    def idx_country_arr(g: int) -> np.ndarray:
        start = (g - 1) * N
        return np.arange(start, start + N)

    def block(M: np.ndarray, g_row: int, g_col: int) -> np.ndarray:
        return M[idx_country_slice(g_row), idx_country_slice(g_col)]

    def L_list_domestic() -> list:
        I = np.eye(N)
        out = [None] * G
        for g in range(1, G + 1):
            ig = idx_country_slice(g)
            A_gg = A[ig, ig]
            out[g - 1] = np.linalg.solve(I - A_gg, I)
        return out

    def get_e_star(s: int) -> np.ndarray:
        """
        e_s* (N,) = rowSums(Z[s, foreign sectors]) + rowSums(Y[s, foreign countries])
        robustly built using np.ix_ to keep 2D slices even if only one foreign country.
        """
        is_arr = idx_country_arr(s)

        start = (s - 1) * N
        end = s * N
        foreign_gn = np.concatenate([np.arange(0, start), np.arange(end, GN)])  # all sectors not in s

        foreign_g_cols = np.array([j for j in range(G) if j != (s - 1)], dtype=int)  # all countries != s

        e_int = Z[np.ix_(is_arr, foreign_gn)].sum(axis=1)               # (N,)
        e_fin = Y[np.ix_(is_arr, foreign_g_cols)].sum(axis=1)           # (N,)
        return np.asarray(e_int + e_fin, dtype=float).ravel()

    # -----------------
    # Precomputes
    # -----------------
    L_list = L_list_domestic()

    # Xexp_list[r-1] = L_rr @ e_r*
    Xexp_list = [None] * G
    for r in range(1, G + 1):
        L_rr = np.asarray(L_list[r - 1], dtype=float)
        e_r_star = get_e_star(r)
        Xexp_list[r - 1] = L_rr @ e_r_star

    rows = []

    # -----------------
    # Main loop (country)
    # -----------------
    for s in range(1, G + 1):
        idx_s = idx_country_slice(s)

        v_s = v[idx_s].ravel()          # (N,)
        X_s = X[idx_s].ravel()          # (N,)
        L_ss = np.asarray(L_list[s - 1], dtype=float)  # (N,N)
        A_ss = A[idx_s, idx_s]          # (N,N)

        Y_ss = Y[idx_s, s - 1].ravel()              # (N,)
        Y_s_tot = Y[idx_s, :].sum(axis=1).ravel()   # (N,)

        # 1) PURE FORWARD (PF): build q_total (N,)
        q_total = np.zeros(N, dtype=float)
        for r in range(1, G + 1):
            if r == s:
                continue
            idx_r = idx_country_slice(r)
            A_sr = A[idx_s, idx_r]                  # (N,N)
            Xexp_r = Xexp_list[r - 1]               # (N,)

            inner = A_sr @ Xexp_r                   # (N,)
            inner_u = A_ss @ (L_ss @ inner)         # (N,)
            q_total += (inner + inner_u)

        PF_vec = v_s * q_total                      # (N,)

        # 2) PURE BACKWARD (PB): intensity terms
        fva_int_total = np.zeros(N, dtype=float)    # Σ v_j' B_js
        fva_int_1border = np.zeros(N, dtype=float)  # Σ v_j' L_jj A_js L_ss

        for j in range(1, G + 1):
            if j == s:
                continue
            idx_j = idx_country_slice(j)
            v_j = v[idx_j].ravel()

            B_js = block(B, j, s)
            fva_int_total += (v_j @ B_js)           # (N,)

            L_jj = np.asarray(L_list[j - 1], dtype=float)
            A_js = block(A, j, s)
            fva_int_1border += (v_j @ (L_jj @ (A_js @ L_ss)))  # (N,)

        PB_vec = (fva_int_total * Y_s_tot) - (fva_int_1border * Y_ss)  # (N,)

        # 3) TWO-SIDED (TS)
        TS_imp_vec = (fva_int_total * X_s) - (fva_int_1border * Y_ss) - PB_vec
        TS_imp_vec = np.where(TS_imp_vec < 0, 0.0, TS_imp_vec)

        term_dom = A_ss @ q_total
        TS_dom_vec = v_s * (L_ss @ term_dom)

        TS_vec = TS_imp_vec + TS_dom_vec
        GVC_vec = PF_vec + PB_vec + TS_vec

        # 4) RESIDUALS
        DomX_vec = v_s * (L_ss @ Y_ss)
        TradX_vec = X_s - DomX_vec - GVC_vec

        cname = countries[s - 1]

        # sectoral rows
        if want_sectoral:
            for i in range(N):
                rows.append({
                    "mode": "total",
                    "country": cname,
                    "sector": sectors[i],
                    "X": float(X_s[i]),
                    "DomX": float(DomX_vec[i]),
                    "TradX": float(TradX_vec[i]),
                    "GVC_PF_X": float(PF_vec[i]),
                    "GVC_PB_X": float(PB_vec[i]),
                    "GVC_TSImp": float(TS_imp_vec[i]),
                    "GVC_TSDom": float(TS_dom_vec[i]),
                    "GVC_TS_X": float(TS_vec[i]),
                    "GVC_X": float(GVC_vec[i]),
                })

        # agg row
        if want_agg:
            rows.append({
                "mode": "total",
                "country": cname,
                "sector": "ALL",
                "X": float(X_s.sum()),
                "DomX": float(DomX_vec.sum()),
                "TradX": float(TradX_vec.sum()),
                "GVC_PF_X": float(PF_vec.sum()),
                "GVC_PB_X": float(PB_vec.sum()),
                "GVC_TSImp": float(TS_imp_vec.sum()),
                "GVC_TSDom": float(TS_dom_vec.sum()),
                "GVC_TS_X": float(TS_vec.sum()),
                "GVC_X": float(GVC_vec.sum()),
            })

    out = pd.DataFrame(rows)

    # ensure base columns and stable ordering
    base_cols = ["mode", "country", "sector"]
    for c in base_cols:
        if c not in out.columns:
            out[c] = np.nan
    out = out.reindex(columns=base_cols + [c for c in out.columns if c not in base_cols])

    # -------------------------
    # Measures
    # -------------------------
    if measures and len(out) > 0:
        Xv = out["X"].to_numpy(float)
        GVCv = out["GVC_X"].to_numpy(float)

        out["share_GVC_output"] = np.where(Xv > 0, out["GVC_X"] / out["X"], np.nan)
        out["share_PF_output"]  = np.where(GVCv > 0, out["GVC_PF_X"] / out["GVC_X"], np.nan)
        out["share_TS_output"]  = np.where(GVCv > 0, out["GVC_TS_X"] / out["GVC_X"], np.nan)
        out["share_PB_output"]  = np.where(GVCv > 0, out["GVC_PB_X"] / out["GVC_X"], np.nan)
        out["forward_output"]   = np.where(GVCv > 0, (out["GVC_PF_X"] - out["GVC_PB_X"]) / out["GVC_X"], np.nan)

    return out


# %%


# %% [markdown]
# ## Up & Downn (Stream)

# %%

def stream(wio) -> pd.DataFrame:
    """
    Compute upstream and downstream indices for each country–sector.

    This function uses:
      - Am : foreign-use technical coefficients matrix (CS × CS)
      - X  : gross output by country–sector (length CS)

    to construct two indicators for each country–sector:
      - 'down' = (I - Amᵀ)^{-1} · 1   (downstreamness)
      - 'up'   = (I - A_scaled)^{-1} · 1, where A_scaled is a
                 row-normalized version of Amᵀ using X (upstreamness).

    Parameters
    ----------
    wio : dict
        Input–output object as returned by `obj_IO`, with at least:
        - wio["Am"]                 : np.ndarray of shape (CS, CS)
        - wio["X"]                  : np.ndarray of length CS
        - wio["dims"]["CS"]         : total number of country–sectors
        - wio["names"]["cs_names"]  : labels for country–sector rows

    Returns
    -------
    result : pandas.DataFrame
        Index: cs_names (country–sector labels)
        Columns:
            - "up"   : upstream stream index
            - "down" : downstream stream index
    """

    # ---- 1. Extract only what we need from wio ----
    Am = np.asarray(wio["Am"], dtype=float)
    X = np.asarray(wio["X"], dtype=float).reshape(-1)
    CS = int(wio["dims"]["CS"])
    cs_names = list(wio["names"]["cs_names"])

    # ---- 2. Basic checks ----
    if Am.shape != (CS, CS):     raise ValueError(f"Am must be of shape ({CS}, {CS}), got {Am.shape}.")
    if X.shape[0] != CS:         raise ValueError(f"X must have length {CS}, got {X.shape[0]}.")
    if len(cs_names) != CS:      raise ValueError(f"cs_names must have length {CS}, got {len(cs_names)}.")

    I = np.eye(CS)

    # ---- 3. Downstream index: (I - Amᵀ)^{-1} * 1 ----
    A_T = Am.T
    result_down = np.linalg.solve(I - A_T, np.ones((CS, 1)))

    # ---- 4. Upstream index: (I - A_scaled)^{-1} * 1 ----
    # Scale Amᵀ by X (avoid division by zero with small epsilon)
    eps = 1e-10
    A_transposed_scaled = ((Am.T * X)).T / (X + eps)
    A_transposed_scaled = np.nan_to_num(A_transposed_scaled)

    M = I - A_transposed_scaled
    result_up = np.linalg.solve(M, np.ones((CS, 1)))

    # ---- 5. Wrap results in a DataFrame ----
    result = pd.DataFrame({"up":   result_up.flatten(), "down": result_down.flatten()}, index=cs_names)

    print("Stream Done!")
    
    return result



# %%


# %% [markdown]
# # 3-B Structural Gravity

# %%

def solve_system(x, T_ratio, q, TI, pi, sigma):
    Y = q
    n =len(q)
    F = np.zeros(n)
    P = np.zeros((n, 1))

    for i in range(n):
        P[i, 0] = np.sum(pi[i].values.reshape(-1, 1) * (x    * T_ratio[i].values.reshape(-1, 1))**(1 - sigma))

    for i in range(n-1):
        F[i] = 1 - np.sum(pi[i:(i+1)].values.reshape(1, -1) * (x[i] * T_ratio[i:(i+1)].values.reshape(1, -1))**(1 - sigma) * (x * Y + TI).T / (P.T * Y[i] * x[i]))

    F[n - 1] = 1 - x[n - 1].item()  

    if np.min(x) <= 0:
        F = F + 1e+3
    
    return F
    
    """
    System of non-linear equations for equilibrium prices with trade imbalances.

    This function builds the vector F(x) such that the equilibrium price vector x
    solves F(x) = 0. It is designed to be used inside a root-finding routine
    (e.g. scipy.optimize.root or fsolve).

    Parameters
    ----------
    x : (n,) array_like
        Current guess for the vector of prices (or price index / multiplier).
        All elements are expected to be strictly positive.

    T_ratio : (n, n) array_like
        Matrix of trade cost ratios T_ij (or T_ij / T_ii), usually with
        T_ii = 1. Row i corresponds to importer i, column j to exporter j.

    q : (n,) array_like
        Vector of incomes / expenditures Y_i.

    TI : (n,) array_like
        Vector of trade imbalances for each country i (can be zero if balanced).

    pi : (n, n) array_like
        Matrix of bilateral expenditure shares π_ij (share of i's expenditure
        spent on goods from j). Row i is importer, column j is exporter.

    sigma : float
        Elasticity of substitution (σ > 1 in standard gravity models).

    Returns
    -------
    F : (n,) ndarray
        Residual vector F(x). At the solution x*, F(x*) ≈ 0. The last equation
        enforces a normalization on x[n-1] (e.g. x[n-1] = 1).

    Notes
    -----
    - Equation i = 0,...,n-2 corresponds to an equilibrium / consistency
      condition for country i.
    - Equation n-1 imposes the normalization: 1 - x[n-1] = 0.
    - If any component of x is non-positive, a large penalty is added to F
      to discourage invalid solutions in numerical solvers.

    Typical usage
    -------------
    >>> from scipy.optimize import root
    >>> n = len(q)
    >>> x0 = np.ones(n)  # initial guess
    >>> res = root(solve_system, x0, args=(T_ratio, q, TI, pi, sigma))
    >>> x_star = res.x
    """


# %%


# %% [markdown]
# ## Grav Panel

# %%
def grav_panel(data: pd.DataFrame, var=None, fe=None, verbose: bool = True):
    
    df = data.copy()

    # defaults
    var = [] if var is None else list(var)
    fe = [] if fe is None else list(fe)

    # # required cols
    # required_cols = {"exporter", "importer", "year", "trade"}
    # missing = required_cols - set(df.columns)
    # if missing:
    #     raise ValueError(f"'data' is missing required columns: {missing}")

    # ensure trade is non-negative (PPML requirement)
    df["trade"] = pd.to_numeric(df["trade"], errors="coerce")
    if df["trade"].isna().any():
        raise ValueError("trade contains NaN after conversion to numeric.")
    if df["trade"].min() < 0:
        print("trade contains negative data converted to 0.")
    df["trade"] = df["trade"].clip(lower=0)

    # build FE identifiers (as strings)
    if "ey" in fe:        df["ey"] = df["exporter"].astype(str) + "_" + df["year"].astype(str)
    if "iy" in fe:        df["iy"] = df["importer"].astype(str) + "_" + df["year"].astype(str)
    if "ei" in fe:        df["ei"] = df["exporter"].astype(str) + "_" + df["importer"].astype(str)
    if "y" in fe:         df["y"] = df["year"].astype(str)
    if "e" in fe:         df["e"] = df["exporter"].astype(str)
    if "i" in fe:         df["i"] = df["importer"].astype(str)

    # DOM/INT indicators (optional as regressors)
    df["DOM"] = (df["exporter"] == df["importer"]).astype(int)
    if "DOM" in fe:         var.append("DOM")
    df["INT"] = (df["exporter"] != df["importer"]).astype(int)
    if "INT" in fe:         var.append("INT")

    # DOM_y / INT_y as FE (recommended if you want year interactions)
    # These are categorical IDs, not dummies.
    if "DOM_y" in fe:
        df["DOM_y"] = df['DOM'].astype(str) + '_' + df['year'].astype(str) 
        df = pd.concat([df, pd.get_dummies(df["DOM_y"], prefix="DOM_y", dtype=int)], axis=1)
        var.extend(df.columns[df.columns.str.startswith("DOM_y_1")].tolist())

    if "INT_y" in fe:
        df["INT_y"] = df['INT'].astype(str) + '_' + df['year'].astype(str) 
        df = pd.concat([df, pd.get_dummies(df["INT_y"], prefix="INT_y", dtype=int)], axis=1)
        var.extend(df.columns[df.columns.str.startswith("INT_y_1")].tolist())


    # keep only FE tokens that correspond to existing columns in df
    fe = [x for x in fe if x not in {"DOM", "INT", "DOM_y", "INT_y"}]
    fe_tokens = [x for x in fe if x in df.columns]

    # de-duplicate FE tokens while preserving order
    seen = set()
    fe_tokens = [x for x in fe_tokens if not (x in seen or seen.add(x))]

    # build formula: if no regressors, use 1
    rhs = " + ".join(var) if len(var) > 0 else "1"
    fe_part = " + ".join(fe_tokens)

    if fe_part == "":
        raise ValueError("No fixed effects specified (fe is empty or not built).")

    fml = f"trade ~ {rhs} | {fe_part}"
    print(fml)

    model = pf.fepois(fml, df, vcov='hetero')

    if verbose:
        print("Model \n", fml)
        print(model.summary())

    return model


# %%


# %% [markdown]
# ## Structural Gravity

# %%
def struc_grav(data,variables,pais_ref):

   
    ############################
    #  B.1 Create variables
    ############################
    data = data.copy()
    #  Create Border BRDR. 1 for domestic trade
    data['BRDR'] = 1 
    data.loc[data['exporter'] == data['importer'], 'BRDR'] = 0
    
    # Create agregate variables Output/Expenditure
    data["output"]  = data.groupby('exporter')['trade'].transform('sum')
    data["expndr"] = data.groupby('importer')['trade'].transform('sum')
    
    # Create fixed effects -> multilateral resistances
    dummies_df = pd.get_dummies(data['exporter'], prefix = "exp_fe", dtype=int)
    data = pd.concat([data, dummies_df], axis=1)
    dummies_df = pd.get_dummies(data['importer'], prefix = "imp_fe", dtype=int)
    data = pd.concat([data, dummies_df], axis=1)
    
    # Adicional parameter: phi, elasticidad de sustitución (en su caso)
    data["phi"] = np.nan
    data.loc[data["exporter"]==data["importer"], "phi"] = data['expndr'] / data['output']
    
    # sigma = 7
    
    columns_names = variables
    
    # Obtener columnas por prefijo EXP
    columnas_exp = list(data.filter(regex='exp_fe_').columns)
    
    # Obtener columnas por prefijo IMP
    columnas_imp = list(data.filter(regex='imp_fe_').columns)
    columnas_imp.remove('imp_fe_'+pais_ref)  #atención aquí se quita el país de refencia
    
    
    # Juntar todas las columnas seleccionadas
    columnas_selec = ["BRDR"] + columns_names + columnas_exp + columnas_imp
    
    # Utilizar las columnas seleccionadas como variables "x" en la regresión
    X = data[columnas_selec]
    
    y = data["trade"]
    
    
    # *************
    # Estimación PYTHON
    # *************
         
    model = sm.GLM(y,X,family=sm.families.Poisson())
    results = model.fit(cov_type='HC3') #errores robustos a la heterocedasticidad HC3
    # print(results.summary())
    params = pd.DataFrame(results.params, columns=['beta_hat'])
    return(results.summary())
    """
    Estimate a structural gravity model (PPML) with exporter and importer fixed effects.

    Parameters
    ----------
    data : pandas.DataFrame
        Bilateral trade data in long format. Must contain at least:
            - 'exporter' : exporter country identifier
            - 'importer' : importer country identifier
            - 'trade'    : bilateral trade flow X_ij

        It must also contain the variables listed in `variables`.

    variables : list of str
        Names of additional explanatory variables already present in `data`
        (e.g. distance, contiguity, trade agreement, common language, etc.).
        Example:
            ['log_dist', 'contig', 'fta', 'currency_union']

    ref_importer : str
        3-letter ISO code (or consistent identifier) of the reference importer.
        The importer fixed effect of this country is dropped to avoid
        perfect multicollinearity (it normalizes the importer MR terms).

    Returns
    -------
    result_dict : dict
        Dictionary with the following keys:
        - 'results' : statsmodels GLMResults object
            Full result object (you can call `.summary()`, `.predict()`, etc.).
        - 'params'  : pandas.DataFrame
            Table of coefficients with:
                - 'beta_hat' : estimated coefficients
                - 'std_err'  : robust standard errors (HC3)
                - 'p_value'  : p-values
        - 'data'    : pandas.DataFrame
            Original data plus constructed variables (output, expndr, FE dummies, phi).
        - 'X'       : pandas.DataFrame
            Regressor matrix used in the estimation.
        - 'y'       : pandas.Series
            Dependent variable ('trade').

    Notes
    -----
    - The model estimated is a Poisson pseudo-maximum likelihood (PPML):
          trade_ij ~ Poisson( exp( X_ij * beta ) )
    - Exporter and importer fixed effects are included to capture
      multilateral resistance terms.
    - BRDR = 1 for international trade, 0 for domestic trade.
    - 'output' is total exports by exporter, 'expndr' is total imports by importer.
    - 'phi' is defined only for domestic trade as expndr_i / output_i.
    - Robust HC3 standard errors are used.

    Example
    -------
    >>> out = struc_grav(
    ...     data=df,
    ...     variables=['log_dist', 'contig', 'fta'],
    ...     ref_importer='USA'
    ... )
    >>> out['results'].summary()
    >>> out['params']
    """

# %%


# %% [markdown]
# ## Structural Grav Contrafactual

# %%
def struc_grav_incre(data,variables,paises1, paises2, pais_ref, increase, sigma):
    """
    Counterfactual 1: One group of countries (countries1) increases
    its trade costs with another group (countries2) by `increase` percent.

    Wrapper around `struc_grav_cf` with selection = 1.
    """
    df = struc_grav_cf(data,variables, paises1, paises2, [], pais_ref, increase, 1, sigma)
    return(df)

def struc_grav_asif(data,variables, paises1, paises2, paises3, pais_ref, sigma):
    """
    Counterfactual 2: "As-if" scenario. One country (or group) in `countries2`
    is made to have the trade costs of another (countries3) vis-à-vis
    a reference group (countries1), often something like the EU.

    Wrapper around `struc_grav_cf` with selection = 2.
    """
    df = struc_grav_cf(data,variables, paises1, paises2, paises3, pais_ref, 0 , 2, sigma)
    return(df)

def struc_grav_inout(data,variables, paises1, paises2, pais_ref, sigma):
    """
    Counterfactual 3: A country enters or exits an RTA (regional trade agreement).

    Wrapper around `struc_grav_cf` with selection = 3.
    """
    df = struc_grav_cf(data,variables, paises1, paises2, [], pais_ref, 0 , 3, sigma)
    return(df)



def struc_grav_cf(data,variables,paises1, paises2, paises3, pais_ref, increase ,seleccion, sigma =7):

    """
    Structural gravity + counterfactual analysis with exact hat algebra.

    This function:
    1. Estimates a baseline PPML structural gravity model with exporter
       and importer fixed effects and border-related variables.
    2. Reconstructs baseline bilateral trade and multilateral resistance terms.
    3. Builds a counterfactual trade cost matrix depending on `selection`.
    4. Solves for the exact general equilibrium counterfactual using `solve_system`.
    5. Returns country-level percentage changes in exports, real income, output,
       and consumption prices.

    Parameters
    ----------
    data : DataFrame
        Bilateral trade data in long format with at least:
            - 'exporter'
            - 'importer'
            - 'trade'
        and gravity covariates in `variables`.

    variables : list of str
        Baseline gravity covariates (e.g. ['LN_DIST', 'CNTG', 'LANG', 'BRDR']).
        Additional dummies are added internally depending on `selection`.

    countries1, countries2, countries3 : list of str
        Groups of countries used to build specific counterfactuals:
        - selection = 1: countries1 vs countries2 (bilateral trade costs increase).
        - selection = 2: “as if” FTA scenario with countries1 (reference group),
          countries2 and countries3.
        - selection = 3: RTA membership change for countries1 and a country in
          countries2.

    ref_country : str
        Reference importer for importer fixed effects (dropped to avoid collinearity).

    increase : float, default 0.0
        Percentage increase in trade costs for selection = 1. Ignored otherwise.

    selection : {1, 2, 3}, default 1
        Type of counterfactual:
            1 -> trade cost increase between groups
            2 -> "as if" FTA scenario
            3 -> country enters/exits RTA

    sigma : float, default 7.0
        Elasticity of substitution.

    verbose : bool, default True
        If True, prints PPML summary and basic checks.

    Returns
    -------
    df_summary : DataFrame
        Country-level summary with columns:
            - Country
            - Export%
            - Real_Income%
            - Output%
            - Cons_Price%

        The full bilateral baseline and counterfactual trade are also stored in
        the internal `data` object created inside this function (accessible if you
        adapt this to return more than df).

    Notes
    -----
    - This function assumes you have a function `solve_system(x, T_ratio, q, TI, pi, sigma)`
      defined elsewhere in your library, implementing the exact-hat equilibrium system.
    """
    ############################
    #  B.1 Create variables
    ############################
    
    #  Create Border BRDR. 1 for domestic trade
    data['BRDR'] = 1 
    data.loc[data['exporter'] == data['importer'], 'BRDR'] = 0
    
    # Create agregate variables Output/Expenditure
    data["output"] = data.groupby('exporter')['trade'].transform('sum')
    data["expndr"] = data.groupby('importer')['trade'].transform('sum')
    
    # Create fixed effects -> multilateral resistances
    dummies_df = pd.get_dummies(data['exporter'], prefix = "exp_fe", dtype=int)
    data = pd.concat([data, dummies_df], axis=1)
    dummies_df = pd.get_dummies(data['importer'], prefix = "imp_fe", dtype=int)
    data = pd.concat([data, dummies_df], axis=1)
    
    # Adicional parameter: phi, elasticidad de sustitución (en su caso)
    data["phi"] = np.nan
    data.loc[data["exporter"]==data["importer"], "phi"] = data['expndr'] / data['output']
    
    
    ####################################################################################
    #       Create border: for 3 different approaches and variables for PPML            #
    ####################################################################################
    
    if seleccion == 1: #Un páís aumenta sus costes de comercio con otro grupo de países un x%
        
        data['BRDR_'+str(len(paises1))+paises2[0]] = (((data['importer'].isin(paises2)) & (data['exporter'].isin(paises1))) |
                       ((data['importer'].isin(paises1)) & (data['exporter'].isin(paises2)))).astype(int)
    
        data['BRDR'] = (data['BRDR'] - data['BRDR_'+str(len(paises1))+paises2[0]]).astype(int)
    
        columns_names = variables+['BRDR_'+str(len(paises1))+paises2[0]]
        
    if seleccion == 2: #Un páís pasa a tener los costes de comercio que tiene otro. Ambos en relación a otro conjunto de países. en nuestro caso UE

        data['if_'+paises2[0]+'_as_'] = (((data['importer'].isin(paises2)) & (data['exporter'].isin(paises1))) |
                                         ((data['importer'].isin(paises1)) & (data['exporter'].isin(paises1)))).astype(int)
        data['ref_'+paises3[0]+'_FTA'] = (((data['importer'].isin(paises3)) & (data['exporter'].isin(paises1))) |
                                         ((data['importer'].isin(paises1)) & (data['exporter'].isin(paises2)))).astype(int)
        data['BRDR'] = (data['BRDR'] - data['if_'+paises2[0]+'_as_'].astype(int) - data['ref_'+paises3[0]+'_FTA']).astype(int)
    
        columns_names = variables+[ 'if_'+paises2[0]+'_as_','ref_'+paises3[0]+'_FTA']
        
    if seleccion == 3: #Un país entra o sale a una RTA
        
        #     Efecto del RTA
        data["RTA"+str(len(paises1))+"_in_out"] =  ((data['importer'].isin(paises1)) & (data['exporter'].isin(paises1)) & (data['importer']!=data['exporter'])).astype(int)
    
        columns_names = variables+["RTA"+str(len(paises1))+"_in_out"]
        
  
        
    # Obtener columnas por prefijo EXP
    columnas_exp = list(data.filter(regex='exp_fe_').columns)
    
    # Obtener columnas por prefijo IMP
    columnas_imp = list(data.filter(regex='imp_fe_').columns)
    columnas_imp.remove('imp_fe_'+pais_ref)  #atención aquí se quita el país de refencia
    
    
    # Juntar todas las columnas seleccionadas
    columnas_selec = columns_names + columnas_exp + columnas_imp
    
    # Utilizar las columnas seleccionadas como variables "x" en la regresión
    X = data[columnas_selec]
    
    y = data["trade"]
    
    
    # *************
    # Estimación PYTHON
    # *************
         
    model = sm.GLM(y,X,family=sm.families.Poisson())
    results = model.fit(cov_type='HC3') #errores robustos a la heterocedasticidad HC3
    print(results.summary())
    params = pd.DataFrame(results.params, columns=['beta_hat'])
    
    
    ####################################################################################
    #    Baseline Index                                             #
    ####################################################################################
    
    # nuevos efectos fijos = antiguos * e^param
    # Eliminar el país de referencia en importacion pues no hay efecto fijo para este país
    
    
    list_countries_exp = data["exporter"].unique()
    for i in list_countries_exp:
        data['exp_fe_' + str(i)] = data['exp_fe_' + str(i)] * np.exp(params.loc[params.index == "exp_fe_"+str(i)].iloc[0,0])
    
    
    list_countries_imp = list(data["importer"].unique())
    list_countries_imp.remove(pais_ref)
    for i in list_countries_imp:
        data['imp_fe_' + str(i)] = data['imp_fe_' + str(i)] * np.exp(params.loc[params.index == "imp_fe_"+str(i)].iloc[0,0])
    
    
    # *Summing for
    data = data.copy()
    data["all_exp_fes_0"] = data.filter(regex=r'^exp_fe_').sum(axis=1)
    data["all_imp_fes_0"] = data.filter(regex=r'^imp_fe_').sum(axis=1)
    
    
    # *Construir los costes de transporte del modelo BLN, tij BLN
    
    t_ij_BLN = np.exp(sum(params.loc[params.index == var].iloc[0, 0] * data[var] for var in columns_names))
    data["t_ij_BLN"] = t_ij_BLN
        
    # *baseline
    data["output_BLN"]=data["output"]
    data["expndr_BLN"]=data["expndr"]
    
    ###########################
    # I.3 Selección del país de referencia
    ############################
    
    # # El efecto fijo será interpretado como gasto.
    data["expndr_0"] = data.loc[data['importer'] == pais_ref, 'expndr'].copy()
    
    # # Rescale all FE creating a variable all values are DEU expenditure
    data["expndr_ref"] = data["expndr_0"].mean()
    
    # *Construir las resistencia multilaterales OMR y IMR.
    data["omr_BLN"]=data["output_BLN"]*data["expndr_ref"]/(data["all_exp_fes_0"])
    data["imr_BLN"]=data["expndr_BLN"]/(data["all_imp_fes_0"]*data["expndr_ref"])
    
    # Hemos recuperado el comercio estimado a partir de los 5 elementos de la ecuación de gravedad (producción, gasto, costes comercio bilateral y terminos estructurales de resistencia multilateral IMR-OMR)
    data["trade_BLN"]=(data["output_BLN"]*data["expndr_BLN"]*data["t_ij_BLN"])/(data["imr_BLN"]*data["omr_BLN"])
    
    
    # Chequeo (la suma del observado y del predicho tiene que ser lo mismo Propiedad de aditividad de la PPML)
    print(data[["trade","trade_BLN"]].sum())
    
    if np.abs((data["trade"].sum() - data["trade_BLN"].sum()))>data["trade"].sum()*0.001: print("Atención: ecuación de gravedad mal identificada.", "\n"," Compruebe la especificación. Por ejemplo: ¿se han estimado todos los efectos fijos?")
    
    data.loc[data["exporter"]!=data["importer"], "exp_BLN"] = data["trade_BLN"]
    data['tot_exp_BLN'] = data.groupby('exporter')['exp_BLN'].transform('sum')
    
    
    
    ####################################################################################
    #        Counterfactual                                              #
    ####################################################################################
    
    if seleccion == 1:
        print(str(paises2) + " increase trade cost with " + str(paises1) + " in  " + str(increase) +"%")
        
        t_ij_CFL = np.exp(sum(params.loc[params.index == var].iloc[0, 0] * data[var] for var in columns_names[:-1])+
                          (1+increase/100)*params.loc[params.index == columns_names[-1]].iloc[0,0]*data[columns_names[-1]])
    
    if seleccion == 2:
        print("If"+ str(paises2) + " behaves as " + str(paises3) + " in relation to " + str(paises1))
        t_ij_CFL = np.exp(sum(params.loc[params.index == var].iloc[0, 0] * data[var] for var in variables)+
                          params.loc[params.index == 'ref_'+paises3[0]+'_FTA'].iloc[0,0]*data['if_'+paises2[0]+'_as_']+
                          params.loc[params.index == 'ref_'+paises3[0]+'_FTA'].iloc[0,0]*data['ref_'+paises3[0]+'_FTA'])
    
    if seleccion == 3:
        paises1_modif = paises1.copy()
        if paises2[0] in paises1: 
            nom_hoja = "_" +str(len(paises1)) + "-" + paises2[0]
            paises1_modif.remove(paises2[0])
            print(str(paises1)+"---OUT---"+str(paises2))
    
        elif paises2[0] not in paises1: 
            nom_hoja = "_" +str(len(paises1)) + "+" + paises2[0]
            paises1_modif.append(paises2[0])
            print(str(paises1)+"---IN---"+str(paises2))
            
                    
        data["NewRTA"] = ((data['importer'].isin(paises1_modif)) & (data['exporter'].isin(paises1_modif)) & (data['importer']!=data['exporter'])).astype(int)

        # Compute t_ij_CFL dynamically
        t_ij_CFL = np.exp(sum(params.loc[params.index == var].iloc[0, 0] * data[var] for var in variables)+
                          params.loc[params.index == "RTA"+str(len(paises1))+"_in_out"].iloc[0,0]*data["NewRTA"])
    
        
    # Assign the computed column to the DataFrame in one step
    data["t_ij_CFL"] = t_ij_CFL
    
    data["t_ij_CFL_1"]=np.log(data["t_ij_CFL"])
    
    
    # ****************************************
    # Solution Exact Hat Algebra *
    # ****************************************
        
    n = data["exporter"].nunique() 
    
    T_bsln = pd.DataFrame(np.array(data["t_ij_BLN"]).reshape(n, n))
    T = pd.DataFrame(np.array(data["t_ij_CFL"]).reshape(n, n)) 
    trade = pd.DataFrame(np.array(data["trade_BLN"]).reshape(n, n))
    
    
    
    # exportaciones bilaterales agregadas por país INI
    own = trade.values.diagonal()
    export_bsln = trade.sum(axis=1) - own
    
    
    
    n=T_bsln.shape[0]
    T_ratio=(T/T_bsln)**(1/(1-sigma));
    q=np.sum(trade,axis=1).values.reshape(-1, 1)
    phi=np.sum(trade,axis=0).values.reshape(-1, 1)/q
    
    
    #     Aditivo
    TI=(phi-1)*q   #Trade imbalance
    E=q+TI
    
    # Realizar el producto de Kronecker entre unos y (q+TI)
    pi = trade/np.kron(np.ones((n, 1)), (q+TI).T)
    
    check_E = np.sum(np.abs(np.sum(trade, axis=0).values.reshape(-1, 1) - (q + TI)))
    print(check_E)
    
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Obtain conuterfactual results %
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    x0=np.ones((n, 1))
    
    sol = optimize.root(solve_system, x0, args=(T_ratio, q, TI, pi, sigma), method='df-sane')
    
    x = sol.x
    
    hat_E=x.reshape(-1, 1)
    hat_Y=x.reshape(-1, 1)
    hat_p=x.reshape(-1, 1)
    
    hat_PInd = np.sum(pi*(np.kron(np.ones((1,n)),hat_p)*T_ratio)**(1-sigma),axis=0).T
    hat_PInd =hat_PInd.values.reshape(-1, 1)
    
    hat_pi= (np.kron(np.ones((1,n)),hat_p)*T_ratio)**(1-sigma)/(np.kron(np.ones((n,1)),hat_PInd.T))
    
    welfare_ACR=((np.diag(hat_pi)**(1/(1-sigma))-1)*100).reshape(-1, 1) #Nota: Es equivalente al cambio en precios de fábrica
    
    welfare_direct=((x.reshape(-1, 1)/hat_PInd**(1/(1-sigma))-1)*100).reshape(-1, 1)
    
    hat_Xij=(hat_pi*(np.kron(np.ones((n,1)),((hat_Y*q+TI)/E).T))-1)*100
    
    trade_c=pi*hat_pi*(np.kron(np.ones((n,1)),(hat_Y*q+TI).T))
    
    # exportaciones bilaterales agregadas por país FIN
    own_c = trade_c.values.diagonal()
    export_c = trade_c.sum(axis=1) - own_c  
    
    
    E_c=np.sum(trade_c,axis=0).values.reshape(-1, 1)
    q_c=np.sum(trade_c,axis=1).values.reshape(-1, 1)
    
    check_q_c=np.sum(np.abs(q_c-(hat_Y*q)))  #ESTE no sale
    check_E_c=np.sum(np.abs(E_c-(hat_Y*q+TI)))
    check_WTI=np.sum(hat_Y*q)-np.sum((hat_Y*q+TI))
    
    x_per=(x-1)*100;
    exp_per = ((export_c/export_bsln)-1)*100
    PInd_per=(hat_PInd**(1/(1-sigma))-1)*100;
    T_per=(T_ratio-1)*100;
    
    print(check_q_c,check_E_c,check_WTI)
    
    
    # Guardar comercio contrafactual    
    trade_c.columns = data.exporter.unique()
    trade_c.index = data.exporter.unique()
    
    trade_c["exporter"] = trade_c.index
    
    
    trade_c = pd.melt(trade_c, id_vars="exporter", var_name='importer', value_name='trade_FLL')
    data = pd.merge(data, trade_c, on=['exporter','importer'])
    
    
    # ****************************************
    # Output  * 
    # ****************************************
    
    df = pd.concat([pd.DataFrame(data.exporter.unique()),pd.DataFrame(exp_per),pd.DataFrame(welfare_direct),
                    pd.DataFrame(x_per),pd.DataFrame(PInd_per)],axis=1)
    
    
    df.columns = ["País","Export%","Renta_Real%","Output%","P_Consumo%"]
    
    print(df)

    return(df)

# %%



