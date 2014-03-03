#!/usr/bin/env ruby

# very rough draft at this time
# I am looking for a simple way to express preconditions (and then post conditions, in fact, the same method can probably be used for both, with an extra arg for 
# desired action proc. i.e.
# conditions [(a>=10), lambda { out, res = some_fun; res } ] lambda {return false}
# conditions [(a>=10), lambda { out, res = some_fun; res } ] lambda {raise "post conditions fail"}
# perhaps the cleanest interface is to just extend Array?

class Object
  def is_bool?
    (self.is_a? TrueClass) || (self.is_a? FalseClass)
  end
end

# first draf: preconditions expects an array of booleans or Procs and returns true only if all the array elements evaluate to true
# Procs can set the value of global variables to share the result of a computation after the preconditions are verified
def preconditions arr
  arr.each {|i|
    if (i.is_bool? && i==false) || (i.is_a?(Proc) && (i.call==false))
      return false
    end
  }
  return true
end

a = [(10 == 10), lambda { true} ]

b = [(10 == 10), lambda {false} ]

c = [(10 == 11), lambda {true} ]

puts preconditions a
puts preconditions b
puts preconditions c

