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

# a = [(10 == 10), lambda { true} ]

# b = [(10 == 10), lambda {false} ]

# c = [(10 == 11), lambda {true} ]

# puts preconditions a
# puts preconditions b
# puts preconditions c

# another approach extending Array, seems nicer? 
class Array
  def all_true?
    self.inject(true) { |res,i| res and ((i==true) || (i.is_a?(Proc) && (i.call==true))) }
  end

  def any_false?
    not self.all_true?
  end

end


# puts "a.all_true? #{a.all_true?}"
# puts "b.all_true? #{b.all_true?}"
# puts "c.all_true? #{c.all_true?}"

# # now lets try to pass a variable

# res = ""
# d = [(10 == 10), lambda {res = "this is true!"; true}]

# puts res if d.all_true?
# puts "error 1 (won't print)" if d.any_false?
# puts "error 2 (will print)" if [lambda{false}, (10==10)].any_false?

# The Array approach is nice but we don't know what filed. The following Hash approach lets you know. 

class Hash

  def all_true?
    self.each { |cond,msg|
        if (cond==false) or (cond.is_a?(Proc) && (cond.call==false))
          return false,msg
        end
    }
    return true,nil
  end

  def any_false?
    res,cause = self.all_true?
    return (not res),cause
  end
end


res, cause = { true => "this is true", 
  false => "this is false"}.all_true?
puts cause if not res


# I think the res, cause = { ... }.all_true? approach can be improved by just raising an exception is something fails. so we can rename all_true to assert in this approach: 

class Hash
  def assert
    self.each { |cond,msg|
        raise msg if (cond==false) or (cond.is_a?(Proc) && (cond.call==false))
    }
  end
end

begin
  puts "Will check preconditions"
  {
    true => "this is true", 
    false => "this is false"
  }.assert
rescue StandardError => e
  puts "caught: #{e.message}"
end

# What would make this prettier is to avoid the hash syntax requirement
