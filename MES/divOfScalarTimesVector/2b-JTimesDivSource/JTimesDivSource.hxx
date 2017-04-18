// *************** Simulation of JTimesDivSource *********************
/* Geometry
 *  x - The radial coordinate (rho)      [nx and dx set from the grid file]
 *  y - The height of the cylinder (z)   [ny and dy set from the grid file]
 *  z - The azimuthal coordinate (theta) [nz and dz set from the grid file and
 *                                        internally in the BOUT++ framework]
 */

#ifndef __JTimesDivSource_H__
#define __JTimesDivSource_H__

#include <bout/constants.hxx> // Gives PI and TWOPI
#include <bout/physicsmodel.hxx>
#include <derivs.hxx>        // Gives the derivatives
#include <difops.hxx>        // Gives the diff options
#include <field_factory.hxx> // Gives field factory
#include <vecops.hxx>        // Gives the vec diff options
// Gives own boundaries (doing so by setting ghost points)
#include "../../../common/BOUTExtensions/include/ownBCs.hxx"
// Gives own operators
#include "../../../common/BOUTExtensions/include/ownOperators.hxx"

class JTimesDivSource : public PhysicsModel {
public:
  // Destructor
  ~JTimesDivSource();

protected:
  int init(bool restarting);
  int rhs(BoutReal t);

private:
  // Global variable initialization
  // ############################################################################
  // Variables
  // *****************************************************************************
  Field3D S_n, phi;
  Field3D S, S_num;
  Field3D e;
  // *****************************************************************************

  // Constants
  // *****************************************************************************
  BoutReal Lx; // The box dimensions
  // *****************************************************************************

  // Make a field group to communicate
  // *****************************************************************************
  FieldGroup com_group;
  // *****************************************************************************

  // Other objects
  // *****************************************************************************
  OwnBCs ownBC;        // Class containing methods which sets the ghost points
  OwnOperators *ownOp; // Class containing own differential operators
  // *****************************************************************************
  // ############################################################################
};

#endif
