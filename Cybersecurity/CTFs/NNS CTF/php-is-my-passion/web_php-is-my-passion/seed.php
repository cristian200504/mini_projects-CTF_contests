<?php
$flag = trim(file_get_contents('/flag.txt'));
$now = time();

$db = new SQLite3('/var/www/data/phpbb.db');
$db->exec('DELETE FROM phpbb_privmsgs');
$db->exec('DELETE FROM phpbb_privmsgs_to');

$stmt = $db->prepare('INSERT INTO phpbb_privmsgs (author_id, message_time, message_subject, message_text, to_address) VALUES (2, :t, :s, :m, :a)');
$stmt->bindValue(':t', $now, SQLITE3_INTEGER);
$stmt->bindValue(':s', 'note to self');
$stmt->bindValue(':m', $flag);
$stmt->bindValue(':a', 'u_2');
$stmt->execute();

$msg_id = $db->lastInsertRowID();
$db->exec("INSERT INTO phpbb_privmsgs_to (msg_id, user_id, author_id, folder_id) VALUES ($msg_id, 2, 2, 0)");
$db->exec("UPDATE phpbb_users SET user_new_privmsg = 1, user_unread_privmsg = 1, user_last_privmsg = $now WHERE user_id = 2");
$db->close();
