htct**btch-orentedss-asse rsarh.

Ech1.gsaarkeataoptions,,,mcprox).
2.Cstructural (gmma, oitioning,crry,t.).
3. Cmbesthese eturs int:
  - An ****(0–100)
   - A ** label**: `STABLE``FRAGILE`, `EXLOSIVE` 
   - A **Pd**: `UP``DOWN`, `NEUTRAL` 
4. Stores scores in  uifie`ast_co` tabe.
5. Opionally expoesdata small geeras a **weekly macr flw report** ssemidsiged o b:

-**Clud-ative (Azure-f,bt potabl)
- Modlar** (eparate eso, fatu, ansring tags)
- **Asset-agnost** (nw asetscbe dded by pluggi into thsme pttern)
-**Reah-orinted** (no execution / trading functionality)zue-Ornd DeplomntAllresliven azureResc Group,forexample:`rg-elerflw`.
###2.1CoreResouc
-Azure CoaerRegisy (ACR)Stoscimage for allj andservc.  -Example:`dealerflowacr.azurecr.io`

****  - Core datastoe fr raw data, featur, adses.  -Example:`pg-dealerflow`

 **Azurevromnt**Hss:**CtarppsJobs**fschdligeion, feur, andsco jobs. **** for the.
- **Azure KeyVault**
Sores scets:
    - Mrketdaa API ky.
   -Posgretion sr.

-**SraAccount o
-Forrawdatadumps,backps, and expots.

### 2.2 Obsrvability

-**og Analytics**
-entralised logging fr Conainrpps&Jbs.

-**Aplicatin Insights**Requmets adrrors fo hAPIsevc.

---## 3. Archtecture

At  hih level:FX Macroseries[  ]   ▼
[ Postges r ][  / Credit+Rates ]     ▼
[ Postgres  ][Job (Istability / Rem/ Directin) ]     ▼
[  ]Reports/4Data Modl

###4.1 aw Tablaw data i stdmp,dnmalisdway frucibility-**aw_options**  `as_of`, `ndrlying`(.g. SPX)
  - `option_ymbl`, `typ`,`stike`, `exiry`unying_ice  `bid`,`sk`, `lt`
- `pen_inest`
- `impid_volatlity`
  - `delta` (nulla– computd if absnt)mma` (nuable)
w_futu_of`, `unyingGOLD)
  - ontt_symbl, `expiry`  `settle_pic`
 - `pe_tet`,`lu`

- **raw_cos_f  `mak` (.g.GOLD,AUD)hedr_lg,`hedger_shr`spe_lo`, `spc_hor`
   `mall_long,`smal_shor`

- **aw_fx**
- `as_of`pre.g. spo_picshr_r_baee.g. AUD shrt rateshort_re_qote.g.  short rateimplied_vl_1m`, `impld_vol_3m` (if avalabl)
raw_mac_rass_of`
   `fd_at
-`ba_at`
raw_cdis_o
 -`hy_ig_sprad_prox`
-`urve_slp_2s10`  `fnding_spd_rxy` (anyohr simp macceditroxieed4Fatue Tes**features_## 4. Azure GPU Orchestration (Hybrid Architecture)
  -`featue_vcr`(JSONB–fulldump)feat_ommodity(perunying day, GOLD)
  `a_of`, `undlyng`heder_net_oiion-`spec_t_sitin`bcwartin_pct-`rll_yid`-`oi_chng`  vol_temstrucure(l)  fe_vector(JSONB)

-**ea_fx**(pe pair pr day, e.g. AUDUSD)  sf,`pair`
- `cot_net_`  tedif(RB–Fed)
  - `cary_tractivnes`
 - `fx__level`  - `fx_vol_slope`- `f_vctor` (JSONB)**crd**
  - as_of`
-`hy_ig_sprd`
- `sprd_nd_1`
 - `funing_proxy`
  - `curv_sop_2s10s`  curv_inversion_dys`
  - `cdit_riksre` (0–1)
  - `cre_regime(e.g.EASY, LATE_CYCLE, STRESS_BUILDIN,DELEVERAGING)

- **_rates**
-`as_of`
  - `fd_ae`
  - `ba_at`  rdif(RB– Fd)
  - `re_diff_3m_change`
  - `liqidity_sco`simple0–1metri from Fed stnce)
  - `ate_egime`(e.g.TIGHT, EASING, CUTTING, NEUTRALUnified ****
  - as_of`(0–1)
  - (0–1)
  -  (0–1optional)
  -  (0–1, optional)credit_risk` (0–1, from features_credit)
  - ` (0–100) – for debugging / extra context
 (Container Apps Jobs)Ech r asmall,statsscontnshedudwith CRON
ingt-otiaa. rows.
da..relevnrfesh for Gold.
..  - On relevant days,refresh`raw_cot`forAUD.

**igest-macro**
  - Fetch Fed & RBA policy rates(ormanull).
  - Fetch imple creditproxes (HY/IG pread proxis, cuve slope).
-Iser `raw_macr_rates` andredi.Input:(,y.daaggretdftu.Ouu:.
Input:,.termstructure,rollyil, nig.
  - Output:faurescommdy.
-**fx-features**
 Input:r_fx`, `wofo AUD.Cmpute rry, positioni FX fas.Oupu:fx.
reditInput:cedi. pread&fundingbasedredirisk_score` ad `crdiregme.
 - Output: feurscret.
-**rates-features**
Input: awmco_r.-Computeratedifrntiatrends, and a simple iquiditycr.Oupu:rates.:
   - Ltet`faues_equty` (SPX)
    - Latt`eatues_cmodity`(GOLD)
    - Latest fx (AUDUSD)  Lat`fatues_credit` and `features_rates`
   For ech aCompute optional , `R_credit`.Combine into a weght.Deiv refrom thresholds.Compute biaand.Compute .Wie.Alightweight HTTP API n b unasa longlivedAzure :
**a-rvr**NAll ndpoints re rea-only and implyexpose data from .


##7.Nbook&Rping
()crHistrinlyss.Plting vetme.Iptcrdigme.Arprgcrp**heweklmwrr(see`REOR_DEIGN.md`dtals).
Saf and Scope Nocdei hrepoconct yrkxchafve trd.llutpue egndahandedcaional sly.Thytm ilbalykptas:  **Bch-oly**oiradymtrucur.  **Rad-ly**frmaarktpspiv(atan, comntyu).