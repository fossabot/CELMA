// *************** Simulation of DDXOverJCylinder *********************
/* Geometry
 *  x - The radial coordinate (rho)
 *  y - The height of the cylinder (z)
 *  z - The azimuthal coordinate (theta)
 */

#include "DDXOverJCylinder.hxx"

// Initialization of the physics
// ############################################################################
int DDXOverJCylinder::init(bool restarting) {
  TRACE("Halt in DDXOverJCylinder::init");

  // Get the option (before any sections) in the BOUT.inp file
  Options *options = Options::getRoot();

  // Load from the geometry
  // ************************************************************************
  Options *geom = options->getSection("geom");
  geom->get("Lx", Lx, 0.0);
  // ************************************************************************

  // Obtain the fields
  // ************************************************************************
  // f
  f = FieldFactory::get()->create3D("f:function", Options::getRoot(), mesh,
                                    CELL_CENTRE, 0);

  // S
  S = FieldFactory::get()->create3D("S:solution", Options::getRoot(), mesh,
                                    CELL_CENTRE, 0);
  // ************************************************************************

  // Add a FieldGroup to communicate
  // ************************************************************************
  // Only these fields will be taken derivatives of
  com_group.add(f);
  // ************************************************************************

  // Set boundaries manually
  // ************************************************************************
  f.setBoundary("f");
  f.applyBoundary();
  ownBC.innerRhoCylinder(f);
  // ************************************************************************

  // Communicate before taking derivatives
  mesh->communicate(com_group);

  output << "\n\n\n\n\n\n\nNow running test" << std::endl;

  // Calculate
  S_num = (1 / mesh->coordinates()->J) * DDX(f);

  // Error in S
  e = S_num - S;

  // Save the variables
  SAVE_ONCE(Lx);
  SAVE_ONCE3(f, S, S_num);
  SAVE_ONCE(e);

  // Finalize
  dump.write();
  dump.close();

  output << "\nFinished running test, now quitting\n\n\n\n\n\n" << std::endl;

  // Wait for all processors to write data
  MPI_Barrier(BoutComm::get());

  return 0;
}
// ############################################################################

// Solving the equations
// ############################################################################
int DDXOverJCylinder::rhs(BoutReal t) { return 0; }
// ############################################################################

// Create a simple main() function
BOUTMAIN(DDXOverJCylinder);

// Destructor
DDXOverJCylinder::~DDXOverJCylinder() {
  TRACE("DDXOverJCylinder::~DDXOverJCylinder");
}