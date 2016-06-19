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

    // Get the option (before any sections) in the BOUT.inp file
    Options *options = Options::getRoot();

    // Create the solver
    // ************************************************************************
    /* NOTE: Calls createOperators without making an object of OwnOperators.
     *       The child is typecasted to the parent
     */
    ownOp = OwnOperators::createOperators();
    ownLapl.create(ownOp, ownBC);
    // As a small hack we find the own operator type to figure out how to
    // treat the div(ue*grad(n grad_perp phi))
    Options *ownOp = options->getSection("ownOperators");
    ownOp->get("type", ownOpType, "simpleStupid");
    // ************************************************************************

    // Create the filter
    // ************************************************************************
    /* NOTE: Calls createFilter without making an object of ownFilter.
     *       The child is typecasted to the parent
     */
    ownFilter = OwnFilters::createFilter();
    // ************************************************************************

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
    cst->get("artHyperAzVortD",  artHyperAzVortD,  0.0);
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
    switches->get("useHyperViscAzVortD", useHyperViscAzVortD, false);
    switches->get("includeNoise"       , includeNoise       , false);
    switches->get("forceAddNoise"      , forceAddNoise      , false);
    switches->get("saveDdt"            , saveDdt            , false);
    switches->get("saveTerms"          , saveTerms          , true );
    noiseAdded = false;
    if (restarting && includeNoise && !(forceAddNoise)){
        output << "\n\n!!!!Warning!!!\n"
               << "restarting = true, includeNoise = true, forceAddNoise = false\n"
               << "Since forceAddNoise = false => program reset includeNoise to false"
               << "\n\n"
               << std::endl;
        includeNoise = false;
        noiseAdded = true; // For extra safety measurements
    }
    // ************************************************************************

    // Calculate diffusion from grid size
    // ************************************************************************
    // SQ is squaring the expression
    // dx and dy are Field2D (0th index is ghost, but gives no problems)
    artViscParLnN   *= SQ(mesh->dy(0,0));
    artViscParUEPar *= SQ(mesh->dy(0,0));
    artViscParUIPar *= SQ(mesh->dy(0,0));
    artViscParVortD *= SQ(mesh->dy(0,0));

    // The perpednicular diffusion is in our model
    /* NOTE: Chosen independent of dz
     *       This makes artVisc constant when expanding restarts
     */
    artViscPerpLnN   *= SQ(mesh->dx(0,0));
    artViscPerpUEPar *= SQ(mesh->dx(0,0));
    artViscPerpUIPar *= SQ(mesh->dx(0,0));
    artViscPerpVortD *= SQ(mesh->dx(0,0));

    // Azimuthal hyperviscosities
    artHyperAzVortD *= SQ(SQ(mesh->dz));
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

    // Split operator
    // ************************************************************************
    /* NOTE: Only active if a split solver is active
     *
     *       Convective is called first (solver.cxx run_rhs)
     *
     *       For implicit-explicit schemes, convective() will typically
     *       be treated explicitly, whilst diffusive() will be treated implicitly.
     *       For unsplit methods, both convective and diffusive will be called
     *       and the sum used to evolve the system:
     *       rhs() = convective() + diffusive()
     *       (comment in physicsmodel.hxx)
     */
    setSplitOperator();
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
    if(saveTerms){
        // lnN terms
        SAVE_REPEAT3(lnNAdv, lnNRes, gradUEPar);
        SAVE_REPEAT4(lnNUeAdv, srcN, lnNParArtVisc, lnNPerpArtVisc);
        // uEPar terms
        SAVE_REPEAT3(uEParAdv, uEParParAdv, gradPhiLnN);
        SAVE_REPEAT4(uEParRes, ueSrc, uEParParArtViscNoN, uEParPerpArtViscNoN);
        SAVE_REPEAT (ueNeutral);
        // uIPar terms
        SAVE_REPEAT3(uIParAdv, uIParParAdv, gradPhi);
        SAVE_REPEAT4(uIParRes, uiSrc, uIParParArtViscNoN, uIParPerpArtViscNoN);
        SAVE_REPEAT (uiNeutral);
        // Vorticity terms
        SAVE_REPEAT2(vortNeutral, potNeutral);
        SAVE_REPEAT3(divParCur, vortDParArtVisc, vortDPerpArtVisc);
        SAVE_REPEAT (parDerDivUIParNGradPerpPhi);

        if(lowercase(ownOpType) == lowercase("simpleStupid")){
            SAVE_REPEAT (divExBAdvGradPerpPhiN);
        }
        else if ( lowercase(ownOpType) == lowercase("onlyBracket") ||
                  lowercase(ownOpType) == lowercase("2Brackets") ){
            SAVE_REPEAT (vortDAdv);

            if (lowercase(ownOpType) == lowercase("2Brackets")){
                SAVE_REPEAT (kinEnAdvN);
            }
        }
        if(saveDdt){
            SAVE_REPEAT4(ddt(vortD), ddt(lnN), ddt(uIPar), ddt(uEPar));
        }
    }
    // Variables to be solved for
    SOLVE_FOR4(vortD, lnN, uIPar, uEPar);
    //*************************************************************************

    return 0;
}
// ############################################################################

// Solving the equations
// ############################################################################
/* The convective part:
 * Should contain all slow dynamics.
 * Will be stepped forward explicitly
 */
// NOTE: The convective part is called first, then the diffusive part
int Celma::convective(BoutReal t) {
    TRACE("Halt in Celma::convective");

    if (includeNoise && !noiseAdded){
        /* NOTE: Positioning of includeNoise
         *
         * As the convective part is calculated first, the addnoise routine
         * will only be needed here.
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
    gradPerpLnN = ownOp->Grad_perp(lnN);
    n = exp(lnN);
    // ************************************************************************

    // Laplace inversion
    // ************************************************************************
    /* NOTE: Solve for phi
     * 1. phi and vort is output
     * 2. The solver takes care of perpendicular boundaries
     * 3. Filtering of higher modes is done internally with the filter flag in
     *    BOUT.inp
     */
    phi = ownLapl.NaulinSolver(gradPerpLnN, n, vortD, phi, vort);
    // Filter
    phi = ownFilter->ownFilter(phi);
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
    gradUEPar      = - DDY(uEPar);
    lnNUeAdv       = - Vpar_Grad_par(uEPar, lnN);
    srcN           =   S/n;
    ddt(lnN) =
          lnNAdv
        + gradUEPar
        + lnNUeAdv
        + srcN
        ;
    // Filtering highest modes
    ddt(lnN) = ownFilter->ownFilter(ddt(lnN));
    // ************************************************************************


    // Terms in uEPar
    // ************************************************************************
    uEParAdv         = - invJ*bracket(phi, uEPar, bm) ;
    uEParParAdv      = - Vpar_Grad_par(uEPar, uEPar) ;
    gradPhiLnN       =   mu*DDY(phi - lnN) ;
    uEParRes         = - 0.51*nuEI *( uEPar - uIPar) ;
    ueNeutral        = - nuEN*uEPar;
    ueSrc            = - S*uEPar/n ;

    ddt(uEPar) =
          uEParAdv
        + uEParParAdv
        + gradPhiLnN
        + uEParRes
        + ueNeutral
        + ueSrc
        ;
    // Filtering highest modes
    ddt(uEPar) = ownFilter->ownFilter(ddt(uEPar));
    // ************************************************************************


    // Terms in uIPar
    // ************************************************************************
    uIParAdv         = - invJ*bracket(phi, uIPar, bm);
    uIParParAdv      = - Vpar_Grad_par(uIPar, uIPar);
    gradPhi          = - DDY(phi);
    uIParRes         = - (0.51*nuEI/mu) *(uIPar - uEPar);
    uiNeutral        = - nuIN*uIPar;
    uiSrc            = - S*uIPar/n;

    ddt(uIPar) =
          uIParAdv
        + uIParParAdv
        + gradPhi
        + uIParRes
        + uiNeutral
        + uiSrc
        ;
    // Filtering highest modes
    ddt(uIPar) = ownFilter->ownFilter(ddt(uIPar));
    // ************************************************************************


    // Preparation
    // ************************************************************************
    DivUIParNGradPerpPhi = ownOp->div_f_GradPerp_g(uIPar*n, phi);
    // Set the ghost points in order to take DDY
    ownBC.extrapolateYGhost(DivUIParNGradPerpPhi);
    // We must communicate as we will take DDY
    mesh->communicate(DivUIParNGradPerpPhi);
    // ************************************************************************


    // Terms in vorticity
    // ************************************************************************
    vortNeutral                = - nuIN*n*vort;
    potNeutral                 = - nuIN*ownOp->Grad_perp(phi)*ownOp->Grad_perp(n);

    if(lowercase(ownOpType) == lowercase("simpleStupid")){
        divExBAdvGradPerpPhiN = - ownOp->div_uE_dot_grad_n_GradPerp_phi(n, phi);
    }
    else if ( lowercase(ownOpType) == lowercase("onlyBracket") ||
              lowercase(ownOpType) == lowercase("2Brackets") ){
        vortDAdv  = - ownOp->vortDAdv(phi, vortD);

        if (lowercase(ownOpType) == lowercase("2Brackets")){
            kinEnAdvN = - ownOp->kinEnAdvN(phi, n);
        }
    }

    parDerDivUIParNGradPerpPhi = - DDY(DivUIParNGradPerpPhi);
    divParCur                  =   DDY(n*(uIPar - uEPar));

    ddt(vortD) =
          vortNeutral
        + potNeutral
        + parDerDivUIParNGradPerpPhi
        + divParCur
        ;

    if(lowercase(ownOpType) == lowercase("simpleStupid")){
        ddt(vortD) += divExBAdvGradPerpPhiN;
    }
    else if ( lowercase(ownOpType) == lowercase("onlyBracket") ||
              lowercase(ownOpType) == lowercase("2Brackets") ){
        ddt(vortD) += vortDAdv;

        if (lowercase(ownOpType) == lowercase("2Brackets")){
            ddt(vortD) += kinEnAdvN;
        }
    }

    // Filtering highest modes
    ddt(vortD) = ownFilter->ownFilter(ddt(vortD));
    // ************************************************************************
    return 0;
}

/* The diffusive part:
 * Should contain all the fast dynamics.
 *
 * What are the fast dynamics
 * --------------------------
 * Other than knowing that diffusion have infinite fast dynamics (only limited
 * by the grid size), and that higher order terms are usually stiff, it is hard
 * to know apriori what terms will contribute to the fast part of the dynamics.
 * What one can do then, is in principle to find the max(ddt(field)), and see
 * if there are any fields which are  much faster than others. These fields can
 * then be put into the diffusive part.
 *
 * The diffusive part will be treated implicitly. This part is usually called
 * several times during a timestep. as there usually will be several newton
 * iterations pr timestep. Therefore, one should have the inversion algorithm
 * here as well
 */
int Celma::diffusive(BoutReal t, bool linear){
    TRACE("Halt in Celma::diffusive");

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
    gradPerpLnN = ownOp->Grad_perp(lnN);
    n = exp(lnN);
    // ************************************************************************

    // Laplace inversion
    // ************************************************************************
    /* NOTE: Solve for phi
     * 1. phi and vort is output
     * 2. The solver takes care of perpendicular boundaries
     * 3. Filtering of higher modes is done internally with the filter flag in
     *    BOUT.inp
     */
    phi = ownLapl.NaulinSolver(gradPerpLnN, n, vortD, phi, vort);
    // Filter
    phi = ownFilter->ownFilter(phi);
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

    // Terms in lnNPar
    // ************************************************************************
    lnNRes         =   (0.51*nuEI/mu) *
                         (Laplace_perp(lnN)+gradPerpLnN*gradPerpLnN);
    lnNParArtVisc  =   artViscParLnN*D2DY2(lnN);
    lnNPerpArtVisc =   artViscPerpLnN*Laplace_perp(lnN);
    ddt(lnN) =
          lnNRes
        + lnNParArtVisc
        + lnNPerpArtVisc
        ;
    // Filtering highest modes
    ddt(lnN) = ownFilter->ownFilter(ddt(lnN));
    // ************************************************************************


    // Terms in uEPar
    // ************************************************************************
    uEParParArtViscNoN  =   (artViscParUEPar)*D2DY2(uEPar);
    uEParPerpArtViscNoN =   (artViscPerpUEPar)*Laplace_perp(uEPar);

    ddt(uEPar) =
          uEParParArtViscNoN
        + uEParPerpArtViscNoN
        ;
    // Filtering highest modes
    ddt(uEPar) = ownFilter->ownFilter(ddt(uEPar));
    // ************************************************************************


    // Terms in uIPar
    // ************************************************************************
    uIParParArtViscNoN  =   (artViscParUIPar)*D2DY2(uIPar);
    uIParPerpArtViscNoN =   (artViscPerpUIPar)*Laplace_perp(uIPar);

    ddt(uIPar) =
          uIParParArtViscNoN
        + uIParPerpArtViscNoN
        ;
    // Filtering highest modes
    ddt(uIPar) = ownFilter->ownFilter(ddt(uIPar));
    // ************************************************************************


    // Preparation
    // ************************************************************************
    DivUIParNGradPerpPhi = ownOp->div_f_GradPerp_g(uIPar*n, phi);
    // Set the ghost points in order to take DDY
    ownBC.extrapolateYGhost(DivUIParNGradPerpPhi);
    // We must communicate as we will take DDY
    mesh->communicate(DivUIParNGradPerpPhi);
    // ************************************************************************


    // Terms in vorticity
    // ************************************************************************
    vortDParArtVisc            =   artViscParVortD*D2DY2(vortD);
    vortDPerpArtVisc           =   artViscPerpVortD*Laplace_perp(vortD);
    if (useHyperViscAzVortD){
        vortDhyperVisc = - artHyperAzVortD*D4DZ4(vortD);
    }
    else{
        vortDhyperVisc = 0.0;
    }

    ddt(vortD) =
          vortDParArtVisc
        + vortDPerpArtVisc
        + vortDhyperVisc
        ;
    // Filtering highest modes
    ddt(vortD) = ownFilter->ownFilter(ddt(vortD));
    // ************************************************************************
    return 0;
}
// ############################################################################

// Create a simple main() function
BOUTMAIN(Celma);