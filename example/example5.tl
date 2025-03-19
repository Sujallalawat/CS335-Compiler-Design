:b = 15
:a = :b + 10
if :b > 30 [
   if :a <= 50 [
      :a = :a * 2
   ] else [
      :a = :a - 5
   ]
] else [
   if :b > 10 [
      :a = :a + 20
   ] else [
      :a = :a - 15
   ]
]
