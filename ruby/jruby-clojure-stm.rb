require "java"
# require "clojure.jar"
# java_import "clojure.lang.LockingTransaction"
# java_import "clojure.lang.Atom"


class Class
  def ref_attr_accessor(*args)
    self.class_eval("
require 'clojure.jar'
java_import 'clojure.lang.LockingTransaction'
java_import 'clojure.lang.Atom'
")

    args.each do |arg|
      self.class_eval("
def #{arg}
   @#{arg}.deref unless @#{arg}.nil? 
end

def #{arg}=(val)
   if @#{arg}.nil?
      @#{arg} = Atom.new(val) 
   else
      @#{arg}.reset val
   end
end
")
      
    end 
  end
end

class ThreadSafeVar
  ref_attr_accessor :id, :name
end

v = ThreadSafeVar.new
v.id = 1
v.name = "test"
puts "meet v: "
puts v.id
puts v.name

puts "now let's fire up concurrent threads to change v.id, and check its value every second while they run"

Thread.new {v.id = v.id + 10; puts "thread 1 done"}
Thread.new {v.id = v.id + 1; puts "thread 2 done"}
Thread.new {v.id = v.id + 5; puts "thread 3 done"}

# give them some time
sleep 2

puts "new value: #{v.id}"

