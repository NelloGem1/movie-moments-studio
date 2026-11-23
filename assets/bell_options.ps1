$sounds = @(
  'C:\Windows\Media\Ring01.wav',
  'C:\Windows\Media\Windows Ding.wav',
  'C:\Windows\Media\Windows Notify System Generic.wav',
  'C:\Windows\Media\Windows Exclamation.wav',
  'C:\Windows\Media\Ring03.wav'
)
foreach ($s in $sounds) {
  (New-Object Media.SoundPlayer $s).PlaySync()
  Start-Sleep -Milliseconds 500
}
