param([Parameter(Mandatory=$true)][string]$Archive,[Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Destination) { throw 'Extraction destination already exists' }
Expand-Archive -LiteralPath $Archive -DestinationPath $Destination
