// *************** Simulation of JTimesDivPerp *********************
/* Geometry
 *  x - The radial coordinate (rho)
 *  y - The height of the cylinder (z)
 *  z - The azimuthal coordinate (theta)
 */

#include "JTimesDivPerp.hxx"

// Initialization of the physics
// ############################################################################
int JTimesDivPerp::init(bool restarting) {
  TRACE("Halt in JTimesDivPerp::init");

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
  f.x = FieldFactory::get()->create3D("fx:function", Options::getRoot(), mesh,
                                      CELL_CENTRE, 0);
  f.y = FieldFactory::get()->create3D("fy:function", Options::getRoot(), mesh,
                                      CELL_CENTRE, 0);
  f.z = FieldFactory::get()->create3D("fz:function", Options::getRoot(), mesh,
                                      CELL_CENTRE, 0);
  f.covariant = false;

  // The source
  S = FieldFactory::get()->create3D("S:Solution", Options::getRoot(), mesh,
                                    CELL_CENTRE, 0);
  // ************************************************************************

  // Add a FieldGroup to communicate
  // ************************************************************************
  // Only these fields will be taken derivatives of
  com_group.add(f);
  // ************************************************************************

  // Set boundaries manually
  // ************************************************************************
  f.x.setBoundary("fx");
  f.y.setBoundary("fy");
  f.z.setBoundary("fz");

  f.x.applyBoundary();
  f.y.applyBoundary();
  f.z.applyBoundary();

  ownBC.innerRhoCylinder(f.x);
  ownBC.innerRhoCylinder(f.y);
  ownBC.innerRhoCylinder(f.z);
  // ************************************************************************

  // Communicate before taking derivatives
  mesh->communicate(com_group);

  // Save the variables
  SAVE_ONCE(Lx);
  SAVE_ONCE3(f, S, S_num);
  SAVE_ONCE(e);

  return 0;
}
// ############################################################################

// Solving the equations
// ############################################################################
int JTimesDivPerp::rhs(BoutReal t) {

  TRACE("JTimesDivPerp::rhs");

  // Calculate
  S_num = mesh->coordinates()->J * Div(f);

  // Error in phi
  e = S_num - S;

  return 0;
}
// ############################################################################

// Create a simple main() function
BOUTMAIN(JTimesDivPerp);

// Destructor
JTimesDivPerp::~JTimesDivPerp() { TRACE("JTimesDivPerp::~JTimesDivPerp"); }
