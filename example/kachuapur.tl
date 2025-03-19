:delta = 5
:i = 0
repeat 3 [
  :i = 1 + :i
  right(90)
  forward(:delta * :i)
]
