import json
import math
import numpy as np
import argparse

# with open('temp.txt', 'r') as f0:
#     temp = f0.readlines()

# root_dir= str(temp[0]).replace('\n', '')
# if_background = int(temp[1])
# #print root_dir+'test', if_background+1


parser = argparse.ArgumentParser()
parser.add_argument("--root_dir", type=str, default='test', \
       help=("Root directory"))
parser.add_argument("--path_dir", type=str, default='/home/junxiang/iPATH2.0', \
       help=("Root directory"))


parser.add_argument("--run_mode", type=int, default='1', \
       help=("run mode:"
        "0 -> set up for acceleration module "
        "1 -> set up for background solar wind"
        "2 -> set up for transport module"))
parser.add_argument("--ranks", type=int, default='10', \
       help=("number of threads for the transport run"))
parser.add_argument("--input", type=str, default='input.json', \
       help=("input file"))
parser.add_argument("--CME_dir", type=str, default='path_output', \
       help=("directory for a specific CME run"))

args = parser.parse_args()

root_dir = args.root_dir
path_dir = args.path_dir
if_background = args.run_mode
ranks = args.ranks


def initial_bndy(data):
        # Generate the initial_bndy file for zeus
        B_AU = data.get('glb') * 1e-9 /bo
        ri   = 1.0  # input location

        if (data.get('x1min') == 0.1):
            v_inner = math.sqrt( data.get('glv') / 430.7) * 0.8231 \
                    * data.get('glv') * 1000. / vo

            ratio = data.get('Omega') * AU / (data.get('glv')*1000.)
            B1_AU = B_AU / math.sqrt(1 + ratio**2.0)
            B3_AU = -1.0 * B1_AU * ratio

            b1 = B1_AU * (ri / data.get('x1min') )**2.
            n_inner = data.get('gln') * (ri/data.get('x1min'))**2. * \
                    data.get('glv')*1000./ v_inner / vo
            ratio_inner = data.get('Omega') * AU * data.get('x1min') / v_inner /vo
            k_inner = data.get('TinMK') * (ri/data.get('x1min'))**(4./3.)
            b3 = -1.0*b1*ratio_inner

            f7 = open(root_dir+"/initial-bndy", "w")
            f7.write("{}  {}  {}  {}  {}\n"
                    .format(n_inner, k_inner, v_inner, b1, b3) )
            if (if_background == 0):
                f7.write("{}  {}  {}  {}  {}\n"
                    .format(n_inner* data.get('n_multi'), k_inner*4./3., 
                    data.get('cme_speed')*1000./vo, b1, b3) )
                f7.write("{}".format(data.get('duration')) )
            f7.close()

        if (data.get('x1min') == 0.05):
            v_inner = math.sqrt( data.get('glv') / 430.7) * 0.8231 \
                    * 0.6* data.get('glv') * 1000. / vo

            ratio = data.get('Omega') * AU / (data.get('glv')*1000.)
            B1_AU = B_AU / math.sqrt(1 + ratio**2.0)
            B3_AU = -1.0 * B1_AU * ratio

            b1 = B1_AU * (ri / data.get('x1min') )**2.
            n_inner = data.get('gln') * (ri/data.get('x1min'))**2. * \
                    data.get('glv')*1000./ v_inner / vo
            ratio_inner = data.get('Omega') * AU * data.get('x1min') / v_inner /vo
            k_inner = data.get('TinMK') * (ri/data.get('x1min'))**(4./3.)
            b3 = -1.0*b1*ratio_inner*0.73

            f7 = open(root_dir+"/initial-bndy", "w")
            f7.write("{}  {}  {}  {}  {}\n"
                    .format(n_inner, k_inner, v_inner, b1, b3) )
            if (if_background == 0):
                f7.write("{}  {}  {}  {}  {}\n"
                    .format(n_inner* data.get('n_multi'), k_inner*4./3., 
                    data.get('cme_speed')*1000./vo, b1, b3) )
                f7.write("{}".format(data.get('duration')) )
            f7.close()

def run_zeus(data):
        #=======================================================================
        #   First create/modify the 3 decks for EDITOR
        #   Note that the number of leading spaces of each line matters
        #   since it's for Fortran
        f2 = open(root_dir+"/chgzeus", "w")
        # this will overwrite the old files        
        f2.write(
            "*read zeus36.mac\n"
            "*define {} \n"
            "*d par.44,45 \n"
            "       parameter     (   in = {},   jn =   1,   kn =   365 ) \n"
            "       parameter     ( nxpx = 500, nypx = 1000, nxrd =   1, nyrd =   1 ) \n"
            .format(str(data.get('FCOMP')), data.get('nbl')+5) )
        if (if_background == 0):
            f2.write(
                "*d par.251,252 \n"
                "       parameter     ( cme_center = 100.0 , cme_width = {}, \n"
                "     1               del_phi = 5.0 , phi_no = {}, shd = 2) \n"
                .format(data.get('cme_width'),
                    int(math.floor(data.get('cme_width')/5.)+7) )
                    )
        f2.write(
            "**make sure to set phi_no as cme_width/del_phi+7 \n"
            "**read chguser")
        f2.close()

        #-------------------------------------> Create the input deck for EDITOR
        f3 = open(root_dir+"/inedit", "w")
        f3.write(""" $editpar   inname='dzeus36', chgdk='chgzeus', idump=1, job=3
          , ipre=1, inmlst=1, iupdate=1, iutask=0, safety=0.10
          , branch='dzeus3.6', xeq='xdzeus36', makename='makezeus'
          , compiler='{0}'
c          , coptions='debug'
          , coptions='optimise'
          , speccopt='-O0', specdk='nmlsts','plot1d','plot2d'
          , libs='checkin.o dnamelist.a dsci01.a grfx03.a psplot.a 
  noncar.a libmfhdf.a libdf.a libz.a libjpeg.a'                      $
c          , libs='checkin.o dnamelist.a dsci01.a grfx03.a psplot.a 
c  noncar.a -L/opt/local/hdf4/{0}/lib -ldf -ljpeg -lz -lsz'          $
c          , libs='checkin.o dnamelist.a dsci01.a grfx03.a psplot.a
c  -L/opt/local/hdf4/{0}/lib -ldf -ljpeg -lz -lsz 
c  -L/opt/local/ncarg/{0}/lib -lncarg -lncarg_gks -lncarg_c
c  -lX11 -lcairo -lfreetype'  
            """.format(str(data.get('FCOMP'))) )
        f3.close()

        #--------------------------------------> Create the input deck for ZEUS.
        f4 = open(root_dir+"/inzeus", "w")        
        f4.write(
 " $iocon    iotty=6, iolog=2                                            $\n")

        if (if_background == 1):
            f4.write(" $rescon   dtdmp=0.1, idtag='{}'               $"
                .format(data.get('idtag')) )
        else:
            resfile_name = 'zr'+ '{:03d}'.format(int(round(data.get('tlim')/0.1))) \
                            + data.get('idtag')
            print (resfile_name)
            f4.write(
                " $rescon   dtdmp=0.1, idtag='{}', resfile='{}'"
                "               $".format(data.get('idtag'), resfile_name) )

        f4.write(
"""
 $ggen1    nbl={}, x1min={} ,x1max={}, igrid=1, x1rat=1.0
            , lgrid=.t.   $
 $ggen2    nbl=1,x2min=90.0,x2max= 91.0, igrid=1, x2rat=1.0, lgrid=.t.,
             units='dg'                                                 $
 $ggen3    nbl=360,x3min=0.0, x3max=360.0, igrid=1, units='dg'
             ,lgrid=.t., x3rat=1.0                                   $
""".format(data.get('nbl'), data.get('x1min'), data.get('x1max'))  )

        if (if_background == 1):
            f4.write(" $pcon     nlim= 999999, tlim={}, ttotal=1.0e+7, tsave=10.0       $"
                .format(data.get('tlim')+0.001) )
        else:
            tlim_CME = data.get('tlim') + data.get('run_time')*3600./t_o
            f4.write(" $pcon     nlim= 999999, tlim={:.3f}, ttotal=1.0e+7, tsave=10.0       $"
                .format(tlim_CME) )

        f4.write(
"""
 $hycon    qcon=1.0, qlin=0.0, courno=0.5, iord=2, istp=0
         , itote=0                                          $
 $iib                                                        $
 $oib                                                        $
 $ijb                                                                  $
 $ojb                                                                  $
 $ikb                                                                  $
 $okb                                                                  $
 $grvcon                                                               $
 $ambcon                                                               $
 $eqos     gamma=1.66666666666667                                      $
 $gcon                                                                 $
 $extcon                                                               $
 $pl1con                                                               $
 $pl2con                                                               $
 $pixcon                                                               $
 $usrcon                                                               $
 $hdfcon   dthdf=0.02, hdfvar='to'                                  $
 $tslcon                                                               $
 $crkcon                                                               $
 $discon                                                               $
 $radcon                                                               $
 $pgen                                                                 $

"""             )
        f4.close()


        #-------------------------------------> Create the macro file zeus36.mac
        f5 = open(root_dir+"/zeus36.mac", "w")
        f5.write(
"""**--+----1----+----2----+----3----+--+----3----+----2----+----1----+----
**                                                                    **
******************  CONDITIONAL COMPILATION SWITCHES  ******************
**                                                                    **
**  1) symmetry axes:  ISYM, JSYM, KSYM
**
*define   JSYM
**
**  2) geometry:  XYZ, or ZRP, or RTP
**
*define   RTP
**
**  3) physics:  AGING, AMBIDIFF, GRAV, ISO, MHD, POLYTROPE, PSGRAV,
**               RADIATION, TWOFLUID
**
*define   MHD
**
**  4) data output modes:  CORKS, DISP, HDF, PIX, PLT1D, PLT2D, RADIO, 
**                         TIMESL
**
*define   PLT2D, TIMESL, HDF
**
**  5) other:  DEBUG, FASTCMOC, HSMOC, MOC, NOMOC, RIEMANN, VECTORISE,
**             CORKS, TWINSHK, PATH, CMEONLY
**
"""             )
        if (if_background == 1):
            f5.write("*define   PATH, CMEONLY")
        else:
            f5.write("*define   PATH")
        
        f5.write("""
**                                                                    **
*************************  MODULE NAME ALIASES  ************************
**                                                                    **
**  The modules "BNDYUPDATE", "SPECIAL", "SPECIALSRC", "SPECIALTRN",
**  "FINISH", "PROBLEM", PROBLEMRESTART", "USERSOURCE", and "USERDUMP" 
**  are slots available for user-developed subroutines.
**
"""             )
        if (if_background == 1):
            f5.write("*alias    BNDYUPDATE       empty")
        else:
            f5.write("*alias    BNDYUPDATE       shkgen")
        
        f5.write("""
*alias    EXTENDGRID       empty
*alias    GRAVITY          empty
*alias    SPECIAL          empty
*alias    SOURCE           srcstep
*alias    SPECIALSRC       empty
*alias    TRANSPORT        trnsprt
*alias    SPECIALTRN       minden
*alias    NEWTIMESTEP      newdt
*alias    NEWGRID          empty
*alias    FINISH           empty
**
*alias    PROBLEM          swind
*alias    ATMOSPHERE       empty
*alias    PROBLEMRESTART   empty
*alias    USERSOURCE       empty
*alias    ARTIFICIALVISC   viscous
*alias    DIFFUSION        empty
*alias    USERDUMP         empty
**                                                                    **
************************  ERROR CRITERIA ALIASES  **********************
**                                                                    **
*alias    GRAVITYERROR     1.0e-6
*alias    GRIDERROR        1.0e-6
*alias    PDVCOOLERROR     1.0e-6
*alias    NEWVGERROR       1.0e-10
*alias    RADIATIONERROR   1.0e-6
**                                                                    **
***********************  ITERATION LIMITS ALIASES  *********************
**                                                                    **
*alias    GRAVITYITER      600
*alias    GRIDITER         20
*alias    PDVCOOLITER      20
*alias    NEWVGITER        20
*alias    RADIATIONITER    20
"""             )
    
        #=======================================================================
        #   Setup  input and initial-bndy
        #
        if (if_background == 0):
            f6 = open(root_dir+"/input", "w")
            f6.write("{} \n1\n0.5\n{}\n{}\n"
                .format(data.get('i_heavy'), data.get('seed_spec'),
                    data.get('inj_rate'))    )

            f6.write("""
! iheavy (1 for CNO, 2 for IRON)
! i_perp (0: Bohm, 1:perp)
! alpha_Iplus ( use 0.5) pre-factor for Gordon-Lee's wave intensity
! seed_spec (use 3.5 for now => E^{-3.5})
! injection rate (use 1.D-2 or lower)
"""                 )
            f6.close()

        initial_bndy(data)

#         #=======================================================================
#         #   Setup  iPATH_zeus.s (to replace the previous dzeus36.s)

#         f8 = open(data.get('root_dir')+"/iPATH_zeus.s", "w")
#         f8.write(
# """setenv SOURCE ../Acceleration
# #=======================================> Get files from home directory.
# if(! -e ./xedit22) cp $SOURCE/editor/xedit22 .
# if(! -e ./dnamelist.a) cp $SOURCE/nmlst/dnamelist.a .
# if(! -e ./dsci01.a) cp $SOURCE/sci/dsci01.a .
# if(! -e ./grfx03.a) cp $SOURCE/grfx/grfx03.a .
# if(! -e ./psplot.a) cp $SOURCE/grfx/psplot.a .
# if(! -e ./noncar.a) cp $SOURCE/grfx/noncar.a .
# #=======================> If necessary, create the directory "dzeus3.6".
# if(! -e ./dzeus3.6) mkdir ./dzeus3.6
# if(! -e ./path_output) mkdir ./path_output

# chmod 755 ./xedit22
# ./xedit22

# make -f ./makezeus
# """             )
#         f8.close()


def setup_transport(data):
        # First change the common.h header file
        f9 = open(path_dir+"/Transport/common.h", "w")
        f9.write(
"""c--------------------    COMMON BLOCK DECLARATION    -------------------

       integer       p_num,        seed_num,     iloop
       integer       p_number,     phi_no,       shell_no    

       parameter     (p_num  = {},  seed_num = {},  iloop  = 60000)
       parameter     (p_number = 400, phi_no = {})

       real*8        mp,           AU,           pi,           eo,
     1               bo,           t_o,          vo,           co,
     2               n_0
       real*8        lcslab_au,    kl_au,        ks_au,        Cturb_AU,
     1               Aq_AU,        lc2d_au,      sslab,        s2d,
     1               C_nu
       real*8        omega,        usw,          br_bnd,       r_bnd,
     1               r0 

       real*8        min_e,        max_e,        r_inner

       real*8        max_p,        min_p,        maxshells,    del_p,
     1               cme_center,   cme_width,    del_phi
       real*8        time_fp,      phi_e,        phi_e_at_inner,
     1               time_start,   time_end,     phi_at_inner

       real*8        energy_0(p_number),  phi_0(phi_no), p_0(p_number)

       real*8        Amass,        Qcharge
               

       COMMON / NORMAL /
     1               mp,           AU,           eo,           pi,
     2               bo,           t_o,          vo,           co,
     3               n_0,          min_e,        max_e,        r_inner,
     4               time_fp,      phi_e,        phi_e_at_inner,
     5               time_start,   time_end,     phi_at_inner
       COMMON / SWIND /
     1               omega,        usw,          br_bnd,       r_bnd,
     2               r0  
       COMMON / TURBULENCE /
     1               lcslab_au,    kL_au,        ks_au,        Cturb_AU,
     2               Aq_AU,        lc2d_au,      sslab,        s2d,
     3               C_nu                                  
       COMMON / ZEUS /
     1               maxshells,    max_p,        min_p,        del_p,
     2               cme_center,   cme_width,    del_phi
       COMMON / DISTR /
     1               energy_0,     phi_0,        p_0,          shell_no
       COMMON / HEAVY /
     1               Amass,        Qcharge  

C---------------     END OF COMMON BLOCK DECLARATION     ---------------
        
        """.format(data.get('p_num'), data.get('seed_num'), 
            int(math.floor(data.get('cme_width')/5.)+5)) )
        f9.close()

        f10 = open(path_dir+"/Transport/trspt_input", "w")
        f10.write(
"""# copy this together with the executable
# observer radial location(AU), longitude (degrees)
{} {}
# Turbulence level at 1AU (db^2/B^2)
{}
# Time resolution, if stop at shock arrival
{} {}
# energy resolution, phi_no
{} {}""".format(data.get('r0_e'), data.get('phi_e'), data.get('cturb_au'),
                72, data.get('if_arrival'), data.get('p_num'), int(math.floor(data.get('cme_width')/5.)+5))    )
        f10.close()

        f11 = open(path_dir+"/Transport/combine.f", "w")
        f11.write(
"""       integer       ranks,        line,        i,            j
       parameter     ( ranks ={}, line ={}*{})
       real*8        fp_data (4, line, ranks),
     1               fp_total (4, line)
       
       character(len=1024) :: filename
      
       do i =1, ranks
         j=i-1+10
         write(filename,"(A3,I4.4)") "fp_", i-1
         open(j, file=filename)
       enddo

       do i=1, ranks
         j=i-1+10
         read(j,*) fp_data(1:4, 1:line, i)
         close(j)  
       enddo

       open(21, file="fp_total", form="formatted")
          
       do j = 1, line        
          do i = 1,4
              fp_total(i,j) = sum(fp_data(i, j, 1:ranks))/ranks

          enddo
c          write(21, "(I2, 3ES14.7)") int(fe_total(1,j)), 
          write(21, 1000) int(fp_total(1,j)), 
     1                      fp_total(2:4,j)
       enddo
       
       close(21)
1000   format(I4, ES25.14E3, ES25.14E3, ES25.14E3)
      end
""".format(ranks, data.get('p_num'), 72 ) )

        f11.close()

#=======================================================================
#=======================================================================
#=======================================================================
#=======================================================================
#=======================================================================
#=======================================================================
#=======================================================================
#=======================================================================

#       some parameters 
AU  = 1.5e11        
eo  = 1.6e-19
pi  = 3.141592653589793116
bo  = 2.404e-9       
t_o = 2858068.3
vo  = 52483.25 
co  = 3.0e8
n_0 = 1.0e6

#      Read input from JSON
with open(args.input) as f:
       data = json.load(f)

# # Solar Wind parameters
# root_dir      = str(data.get('get('root_dir'))
# nbl           = data.get('get('nbl')
# x1min         = data.get('get('x1min')
# x1max         = data.get('get('x1max')
# idtag         = data.get('get('idtag')
# tlim          = data.get('get('tlim')
# FCOMP         = str(data.get('get('FCOMP'))
# gln           = data.get('get('gln')
# TinMK         = data.get('get('TinMK')
# glv           = data.get('get('glv')
# glb           = data.get('get('glb')
# Omega         = data.get('get('Omega')

# # CME parameters
# i_heavy       = data.get('get('i_heavy')
# seed_spec     = data.get('get('seed_spec')
# inj_rate      = data.get('get('inj_rate')
# run_time      = data.get('get('run_time')
# cme_speed     = data.get('get('cme_speed')
# cme_width     = data.get('get('cme_width')
# duration      = data.get('get('duration')
# n_multi       = data.get('get('n_multi')

# # Transport Setup
# p_num         = data.get('get('p_num')
# t_num         = data.get('get('t_num')
# seed_num      = data.get('get('seed_num')
# if_arrival    = data.get('get('if_arrival')
# r0_e          = data.get('get('r0_e')
# phi_e         = data.get('get('phi_e')
# cturb_au      = data.get('get('cturb_au')
# MPI_compiler  = str(data.get('get('MPI_compiler'))


#=======================================================================
#      Setting up solar wind

if if_background ==0:
    run_zeus(data)
    print ('Acceleration module done')

if if_background ==1:
    run_zeus(data)
    print ('Setting up Solar wind done')

if if_background ==2:
    setup_transport(data)
    print ('Setting up Transport done')






