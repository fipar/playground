#!/usr/bin/env ruby

# very rough draft at this time
# I am looking for a simple way to express preconditions (and then post conditions, in fact, the same method can probably be used for both, with an extra arg for 
# desired action proc. i.e.
# conditions [(a>=10), lambda { out, res = some_fun; res } ] lambda {return false}
# conditions [(a>=10), lambda { out, res = some_fun; res } ] lambda {raise "post conditions fail"}

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

# another approach extending Array, seems nicer? 
class Array
  def all_true?
    self.inject(true) { |res,i| res and ((i==true) || (i.is_a?(Proc) && (i.call==true))) }
  end

  def any_false?
    not self.all_true?
  end

end


puts "a.all_true? #{a.all_true?}"
puts "b.all_true? #{b.all_true?}"
puts "c.all_true? #{c.all_true?}"

# now lets try to pass a variable

res = ""
d = [(10 == 10), lambda {res = "this is true!"; true}]

puts res if d.all_true?
puts "error 1 (won't print)" if d.any_false?
puts "error 2 (will print)" if [lambda{false}, (10==10)].any_false?

# TODO: 
# finally, not time now, but I think the array could actually be a Hash (since the order of preconditions should not matter), with condition as key, and message as value. 
# that way, we inject on a tuple-like variable, where we store the res and <expr> boolean result, and a concatenation of string messages, so that if the boolean part
# of the tuple is false, we can do something with the concatenated messages, and the caller knows every item that failed. 

