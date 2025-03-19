:sum = 0
:product = 1
:a = 10
:b = :a

if :a / 2 == 0 [
   :product = :product * :b
] else [
   :sum = :sum + 5
]

:a = :sum

if :a > 5 [
      :sum = :sum - 3
      if :b / 3 == 0 [
         :product = :product + :a
      ]
] else [
    :sum = :sum * 2
    :product = :product - :a 
]
   
:c = :product
:sum = :sum + :c

