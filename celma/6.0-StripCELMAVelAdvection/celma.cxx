// *************** Simulation of CELMA *********************
/* Geometry
 *  x - The radial coordinate (rho)
 *  y - The height of the cylinder (z)
 *  z - The azimuthal coordinate (theta)
 */

#include "celma.hxx"

// Initialization of the physics
// ############################################################################
int Celma::init(bool restarting) {
    TRACE("Halt in Celma::init");

    // Create the solver
    // ************************************************************************
    ownLapl.create(ownOp, ownBC);
    // ************************************************************************

    // Get the option (before any sections) in the BOUT.inp file
    Options *options = Options::getRoot();

    // Get the constants
    // ************************************************************************
    // Get the section of the variables from [cst] specified in BOUT.inp
    // or in the command-line arguments
    Options *cst = options->getSection("cst");
    // Storing the variables with the following syntax
    // sectionName->get("nameInInp", varNameInCxx, defaultVal)
    cst->get("mu",               mu,               0.0);
    cst->get("Lambda",           Lambda,           0.0);
    cst->get("nuEI",             nuEI,             0.0);
    cst->get("nuEN",             nuEN,             0.0);
    cst->get("nuIN",             nuIN,             0.0);
    cst->get("artViscParLnN",    artViscParLnN,    0.0);
    cst->get("artViscParUEPar",  artViscParUEPar,  0.0);
    cst->get("artViscParUIPar",  artViscParUIPar,  0.0);
    cst->get("artViscParVortD",  artViscParVortD,  0.0);
    cst->get("artViscPerpLnN",   artViscPerpLnN,   0.0);
    cst->get("artViscPerpUEPar", artViscPerpUEPar, 0.0);
    cst->get("artViscPerpUIPar", artViscPerpUIPar, 0.0);
    cst->get("artViscPerpVortD", artViscPerpVortD, 0.0);
    // ************************************************************************

    // Get the source constants
    // ************************************************************************
    Options *src = options->getSection("src");
    src->get("a",    a,    0.0);
    src->get("bRho", bRho, 0.0);
    src->get("bZ",   bZ,   0.0);
    src->get("cRho", cRho, 0.0);
    src->get("cZ",   cZ,   0.0);
    // ************************************************************************

    // Get the switches
    // ************************************************************************
    Options *switches = options->getSection("switch");
    switches->get("includeNoise", includeNoise, false);
    noiseAdded = false;
    // ************************************************************************

    // Calculate diffusion from grid size
    // ************************************************************************
    // SQ is squaring the expression
    // dx and dy are Field2D (0th index is ghost, but gives no problems)
    artViscParLnN   *= SQ(mesh->dy(0,0));
    artViscParUEPar *= SQ(mesh->dy(0,0));
    artViscParUIPar *= SQ(mesh->dy(0,0));
    artViscParVortD *= SQ(mesh->dy(0,0));

    // The perpednicular diffusion is in our model never hyper
    artViscPerpLnN   *= SQ(mesh->dx(0,0) + mesh->dz);
    artViscPerpUEPar *= SQ(mesh->dx(0,0) + mesh->dz);
    artViscPerpUIPar *= SQ(mesh->dx(0,0) + mesh->dz);
    artViscPerpVortD *= SQ(mesh->dx(0,0) + mesh->dz);
    // ************************************************************************

    // Load from the geometry
    // ************************************************************************
    Options *geom = options->getSection("geom");
    geom->get("Lx", Lx, 0.0);
    geom->get("Ly", Ly, 0.0);
    // ************************************************************************

    // Additional fields
    // ************************************************************************
    // The source (obtained from the input)
    S = FieldFactory::get()
      ->create3D("theSource:S", Options::getRoot(), mesh, CELL_CENTRE, 0);

    // The radial profile (obtained from the input)
    dampingProfile = FieldFactory::get()
      ->create3D("dampProf:profile", Options::getRoot(), mesh, CELL_CENTRE, 0);

    // The initial potential (obtained from the input)
    phi = FieldFactory::get()
          ->create3D("phi:function", Options::getRoot(), mesh, CELL_CENTRE, 0);

    // The metric coefficient (needed in front of the arakawa bracket)
    invJ = (1.0/mesh->J);
    // ************************************************************************

    // Specifying the brackets to the arakawa scheme
    // (see examples/MMS/hw for a elegant way to choose from the input file)
    // ************************************************************************
    bm = BRACKET_ARAKAWA;
    // ************************************************************************

    // Add a FieldGroup to communicate
    // ************************************************************************
    // NOTE: We only communicate variables we are taking derivatives of
    comGroup.add(lnN);
    comGroup.add(n);
    comGroup.add(uIPar);
    comGroup.add(uEPar);
    comGroup.add(phi);
    comGroup.add(vortD);
    // ************************************************************************

    // Specify what values should be stored in the .dmp file
    // ************************************************************************
    // Variables to be saved once
    // Constants
    SAVE_ONCE2(mu, Lambda);
    SAVE_ONCE3(nuEI, nuEN, nuIN);
    SAVE_ONCE5(a, bRho, bZ, cRho, cZ);
    SAVE_ONCE2(Lx, Ly);
    SAVE_ONCE4(artViscParLnN, artViscParUEPar, artViscParUIPar, artViscParVortD);
    SAVE_ONCE4(artViscPerpLnN, artViscPerpUEPar, artViscPerpUIPar, artViscPerpVortD);
    // Fields
    SAVE_ONCE2(S, dampingProfile);
    // Variables to be saved repeatedly
    // vort and phi
    SAVE_REPEAT2(vort, phi);
    // lnN terms
    SAVE_REPEAT3(lnNAdv, lnNRes, gradUEPar);
    SAVE_REPEAT4(lnNUeAdv, srcN, lnNParArtVisc, lnNPerpArtVisc);
    // uEPar terms
    SAVE_REPEAT2(uEParAdv, gradPhiLnN);
    SAVE_REPEAT4(uEParRes, uESrc, uEParParArtVisc, uEParPerpArtVisc);
    SAVE_REPEAT (uENeutral);
    // uIPar terms
    SAVE_REPEAT2(uIParAdv, gradPhi);
    SAVE_REPEAT4(uIParRes, uISrc, uIParParArtVisc, uIParPerpArtVisc);
    SAVE_REPEAT (uINeutral);
    // Vorticity terms
    SAVE_REPEAT2(vortNeutral, potNeutral);
    SAVE_REPEAT2(divExBAdvGradPerpPhiN, parDerDivUIParNGradPerpPhi)
    SAVE_REPEAT4(nGradUIUE, UIUEGradN, vortDParArtVisc, vortDPerpArtVisc);
    // Variables to be solved for
    SOLVE_FOR4(vortD, lnN, uIPar, uEPar);
    //*************************************************************************

    return 0;
}
// ############################################################################

// Solving the equations
// ############################################################################
int Celma::rhs(BoutReal t) {
    TRACE("Halt in Celma::rhs");

    if (includeNoise && !noiseAdded){
        /* NOTE: Positioning of includeNoise
         *
         * If the add noise is going to be called when doing a restart, the
         * includeNoise must be added in the rhs
         *
         * int main(int argc, char **argv)
         *    # Solver *solver = Solver::create();
         *    # solver->setModel(model);                  # Call of model init
         *    # solver->addMonitor(bout_monitor, Solver::BACK);
         *    # solver->outputVars(dump);                 # Call of load restart files
         *    # solver->solve();
         *int Solver::solve(int NOUT, BoutReal TIMESTEP)
         *int PvodeSolver::init(bool restarting, int nout, BoutReal tstep)
         *    # Around line 83 there is the call
         *    # if(Solver::init(restarting, nout, tstep)){
         *    # This loads the restart files
         *void solver_f(integer N, BoutReal t, N_Vector u, N_Vector udot, void *f_data
         *PvodeSolver::rhs(int N, BoutReal t, BoutReal *udata, BoutReal *dudata)
         *Solver::run_rhs(BoutReal t)
         *int PhysicsModel::runRHS(BoutReal time)
         *int Celma::rhs(BoutReal t)
         */
        // Class containing the noise generators
        // Calls the constructor with default arguments
        NoiseGenerator noise("geom", 3);
        // Add noise
        //*********************************************************************
        noise.generateRandomPhases(lnN, 1.0e-3);
        //*********************************************************************

        // Declare that the noise has been added
        noiseAdded = true;
    }

    // Manually specifying rho inner ghost points
    // ************************************************************************
    ownBC.innerRhoCylinder(lnN);
    ownBC.innerRhoCylinder(uEPar);
    ownBC.innerRhoCylinder(uIPar);
    ownBC.innerRhoCylinder(phi);    // Used to set BC in lapalace inversion
    ownBC.innerRhoCylinder(vortD);  // Later taken derivative of
    // The inner boundaries of phi is set in the inversion procedure
    // ************************************************************************

    // Preparations
    // ************************************************************************
    /* NOTE: Preparations
     * 1. gradPerp(lnN) is input to the NaulinSolver , thus
     *    a) gradPerpLnN needs to be calculated...
     *    b) ...which requires that lnN has been communicated
     * 2. n is input to the NaulinSolver, so
     *    a) It needs to be calculated
     *    b) We will communicate as the derivative is needed in vortD
     *
     * Note also:
     * 1. No further derivatives is taken for GradPerp(lnN), so this is not
     *    needed to be communicated.
     * 2. We are taking the derivative of phi in the NaulinSolver, however,
     *    this happens in a loop, and it is communicated before taking the
     *    derivative
     */
    mesh->communicate(lnN);
    gradPerpLnN = ownOp.Grad_perp(lnN);
    n = exp(lnN);
    // ************************************************************************

    // Laplace inversion
    // ************************************************************************
    /* NOTE: Solve for phi
     * 1. phi and vort is output
     * 2. The solver takes care of perpendicular boundaries
     */
    phi = ownLapl.NaulinSolver(gradPerpLnN, n, vortD, phi, vort);
    // ************************************************************************

    // Treating parallel boundary conditions
    // ************************************************************************
    /* NOTE: No boundary condition on phi
     * - We need to know the parallel ghost point of phi, as we are using the
     *   Grad_par(phi) to calculate uEPar.
     * - phi is not an evolved variable.
     * - Setting a boundary condition on this would be to constrain the result.
     * - Extrapolation is used instead.
     */
    ownBC.extrapolateYGhost(phi);
    // Use the sheath boundary condition with constant Te for uEPar at SE
    // Here we have phiRef = Lambda
    ownBC.uEParSheath(uEPar, phi, Lambda, Lambda, dampingProfile);
    // ************************************************************************

    // Communicate before taking derivatives
    mesh->communicate(comGroup);

    /* NOTE: Bracket operator
     * The bracket operator returns -(grad(phi) x b/B)*grad(f)
     * As B is defined by in field aligned coordinates, and we are working with
     * cylindrical coordinates (which happens to coincide with the metrics of
     * that of the field aligned coordinate system) we need to multiply with
     * 1/J
     */

    // Terms in lnNPar
    // ************************************************************************
    lnNAdv         = - invJ*bracket(phi, lnN, bm);
    lnNRes         =   (0.51*nuEI/mu) *
                         (Laplace_perp(lnN)+gradPerpLnN*gradPerpLnN);
    gradUEPar      = - Grad_par(uEPar);
    lnNUeAdv       = - Vpar_Grad_par(uEPar, lnN);
    srcN           =   S/n;
    lnNParArtVisc  =   artViscParLnN*D2DY2(lnN);
    lnNPerpArtVisc =   artViscPerpLnN*Laplace_perp(lnN);
    ddt(lnN) =   lnNAdv
                + lnNRes
                + gradUEPar
                + lnNUeAdv
                + srcN
                + lnNParArtVisc
                + lnNPerpArtVisc
                ;
    // ************************************************************************


    // Terms in uEPar
    // ************************************************************************
    uEParAdv         = - invJ*bracket(phi, uEPar, bm) ;
    gradPhiLnN       =   mu*Grad_par(phi - lnN) ;
    uEParRes         = - 0.51*nuEI *( uEPar - uIPar) ;
    uENeutral        = - nuEN*uEPar;
    uESrc            = - S*uEPar/n ;
    uEParParArtVisc  =   artViscParUEPar*D2DY2(uEPar)/n;
    uEParPerpArtVisc =   (artViscPerpUEPar/n)*Laplace_perp(uEPar);

    ddt(uEPar) =
          uEParAdv
        + gradPhiLnN
        + uEParRes
        + uENeutral
        + uESrc
        + uEParParArtVisc
        + uEParPerpArtVisc
        ;
    // ************************************************************************


    // Terms in uIPar
    // ************************************************************************
    uIParAdv         = - invJ*bracket(phi, uIPar, bm);
    gradPhi          = - Grad_par(phi);
    uIParRes         = - (0.51*nuEI/mu) *(uIPar - uEPar);
    uINeutral        = - nuIN*uIPar;
    uISrc            = - S*uIPar/n;
    uIParParArtVisc  =   artViscParUIPar*D2DY2(uIPar)/n;
    uIParPerpArtVisc =   (artViscPerpUIPar/n)*Laplace_perp(uIPar);

    ddt(uIPar) =
          uIParAdv
        + gradPhi
        + uIParRes
        + uINeutral
        + uISrc
        + uIParParArtVisc
        + uIParPerpArtVisc
        ;
    // ************************************************************************


    // Preparation
    // ************************************************************************
    DivUIParNGradPerpPhi = ownOp.div_f_GradPerp_g(uIPar*n, phi);
    // Set the ghost points in order to take DDY
    ownBC.extrapolateYGhost(DivUIParNGradPerpPhi);
    // We must communicate as we will take DDY
    mesh->communicate(DivUIParNGradPerpPhi);
    // ************************************************************************


    // Terms in vorticity
    // ************************************************************************
    vortNeutral                = - nuIN*n*vort;
    potNeutral                 = - nuIN*ownOp.Grad_perp(phi)*ownOp.Grad_perp(n);
    divExBAdvGradPerpPhiN      = - ownOp.div_uE_dot_grad_n_GradPerp_phi(n, phi);
    parDerDivUIParNGradPerpPhi = - DDY(DivUIParNGradPerpPhi);
    nGradUIUE                  =   Vpar_Grad_par(n, uIPar - uEPar);
    UIUEGradN                  =   Vpar_Grad_par(uIPar - uEPar, n);
    vortDParArtVisc            =   artViscParVortD*D2DY2(vortD);
    vortDPerpArtVisc           =   artViscPerpVortD*Laplace_perp(vortD);

    ddt(vortD) =
              vortNeutral
            + potNeutral
            + divExBAdvGradPerpPhiN
            + parDerDivUIParNGradPerpPhi
            + nGradUIUE
            + UIUEGradN
            + vortDParArtVisc
            + vortDPerpArtVisc
            ;
    // ************************************************************************
    return 0;
}
// ############################################################################

// Create a simple main() function
BOUTMAIN(Celma);