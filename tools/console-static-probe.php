<?php
// Read-only static hosting probe. No credentials. Diagnostics printed to Render logs.
$base = 'https://v075-preview.fleetbase.pages.dev';
function probe($url) {
  $context = stream_context_create(['http'=>['timeout'=>14,'ignore_errors'=>true,'follow_location'=>true,'max_redirects'=>3,'header'=>"User-Agent: FleetbaseStageDiag/1.0\r\n"]]);
  $body=@file_get_contents($url,false,$context);
  $headers=$http_response_header??[];
  $status='none';$ctype='unknown';
  foreach ($headers as $h) {
    if(preg_match('/^HTTP\/\S+\s+(\d+)/i',$h,$m)) $status=$m[1];
    if(stripos($h,'content-type:')===0) $ctype=trim(substr($h,13));
  }
  return [$status,$ctype,($body===false?'':$body),$headers];
}
[$s,$t,$html]=probe($base.'/onboard');
echo "[console-probe] /onboard status={$s} type={$t} bytes=".strlen($html)."\n";
if(preg_match('/<title[^>]*>(.*?)<\/title>/is',$html,$m)) echo "[console-probe] title=".trim(strip_tags($m[1]))."\n";
if(!preg_match('/<html/i',$html)) echo "[console-probe] WARNING: no HTML root\n";
$urls=[];
preg_match_all('/<(?:script|link)\b[^>]*(?:src|href)\s*=\s*["\x27]([^"\x27]+)["\x27]/i',$html,$m);
foreach($m[1] as $asset) {
 if(!preg_match('/\.(js|css)(?:\?|$)/i',$asset))continue;
 $url=str_starts_with($asset,'http')?$asset:$base.'/'.ltrim($asset,'/');
 $urls[]=$url;
}
$urls=array_slice(array_unique($urls),0,24);
foreach($urls as $u) {
 [$st,$ct,$body]=probe($u);
 $path=parse_url($u,PHP_URL_PATH);
 echo "[console-probe] asset {$path} status={$st} type={$ct} bytes=".strlen($body)."\n";
 if(preg_match('/\.js$/i',$path)&&str_contains(strtolower($ct),'text/html'))echo "[console-probe] ERROR: Javascript asset served as HTML\n";
}
[$s,$ct,$body]=probe($base.'/fleetbase.config.json');
echo "[console-probe] fleetbase.config.json status={$s} type={$ct} bytes=".strlen($body)."\n";
if($s==='200'){
 $json=json_decode($body,true);
 if(is_array($json)){
   foreach(['API_HOST','API_SECURE','DISABLE_RUNTIME_CONFIG','SOCKETCLUSTER_HOST'] as $key)
     if(array_key_exists($key,$json))echo "[console-probe] config {$key}=".substr((string)$json[$key],0,120)."\n";
 } else echo "[console-probe] WARNING: config JSON invalid\n";
}
[$s,$ct,$body]=probe($base.'/auth');
echo "[console-probe] /auth status={$s} type={$ct} bytes=".strlen($body)."\n";
