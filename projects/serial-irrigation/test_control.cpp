#include "control.h"
#include <cassert>
#include <limits>
int main() {
  assert(irrigationCommand(0)=='1');
  assert(irrigationCommand(306)=='1');
  assert(irrigationCommand(307)=='0');
  assert(irrigationCommand(1023)=='0');
  ValveControl v;
  assert(!v.update(0));
  v.receive('1',100); assert(v.update(1100)); assert(!v.update(1101));
  v.receive('1',2000); v.receive('x',2001); assert(!v.update(2001));
  v.receive('1',3000); v.receive('0',3001); assert(!v.update(3001));
  unsigned long nearWrap=std::numeric_limits<unsigned long>::max()-500UL;
  v.receive('1',nearWrap); assert(v.update(100UL)); assert(!v.update(1000UL));
}
