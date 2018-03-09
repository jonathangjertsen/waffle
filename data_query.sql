-- Export result of this query as CSV.

SELECT `mw`.*, `u`.`username`
FROM `mod_waffle` `mw`
INNER JOIN `users` `u` ON `u`.`id`=`mw`.`uid`
WHERE `mw`.`wafflecount` != 0
ORDER BY `mw`.`consumed` ASC
