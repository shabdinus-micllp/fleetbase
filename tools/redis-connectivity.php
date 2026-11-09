<?php
// Read-only network diagnostic for Render staging; never prints passwords.
// Run inside the Fleetbase API container: php tools/redis-connectivity.php
$host = getenv('REDIS_HOST') ?: 'red-dbno55ec6qcc73edudv0';
$port = filter_var(getenv('REDIS_PORT') ?: '6379', FILTER_VALIDATE_INT) ?: 6379;
$start = microtime(true);
echo "[redis-diagnostic] starting\n";
$resolved = gethostbyname($host);
echo "[redis-diagnostic] system resolver: " . ($resolved === $host ? "unresolved" : "resolved") . "\n";
$records = @dns_get_record($host, DNS_A | DNS_AAAA);
if (!is_array($records) || !$records) {
    echo "[redis-diagnostic] DNS: no A/AAAA records\n";
} else {
    foreach ($records as $record) {
        $addr = $record['ip'] ?? $record['ipv6'] ?? null;
        if ($addr) echo "[redis-diagnostic] DNS: " . (filter_var($addr, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6) ? 'AAAA' : 'A') . " record present\n";
    }
}
$errNo = 0; $errStr = '';
$socket = @stream_socket_client("tcp://{$host}:{$port}", $errNo, $errStr, 5, STREAM_CLIENT_CONNECT);
if ($socket === false) {
    echo "[redis-diagnostic] TCP: FAILED code={$errNo} reason=" . preg_replace('/[^a-zA-Z0-9 .:_-]/', '', $errStr) . "\n";
    exit(2);
}
echo "[redis-diagnostic] TCP: CONNECTED in " . round(microtime(true)-$start, 3) . "s\n";
stream_set_timeout($socket, 3);
fwrite($socket, "*1\r\n\$4\r\nPING\r\n");
$response = fgets($socket, 512);
$info = stream_get_meta_data($socket);
if ($info['timed_out']) echo "[redis-diagnostic] PING: timed out\n";
elseif (str_starts_with((string) $response, '+PONG')) echo "[redis-diagnostic] PING: PONG\n";
elseif (str_starts_with((string) $response, '-NOAUTH')) echo "[redis-diagnostic] PING: authentication required (TCP connectivity OK)\n";
elseif (str_starts_with((string) $response, '-')) echo "[redis-diagnostic] PING: Redis error (details intentionally hidden)\n";
else echo "[redis-diagnostic] PING: unexpected response or connection closed\n";
fclose($socket);
