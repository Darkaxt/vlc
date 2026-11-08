# Read the already hash-bound keg recipe with Homebrew's native DSL. Older
# bottles predate SPDX SBOMs; never substitute today's API formula or a bottle.
require "json"
require "formula"
require "formulary"

recipe, expected_version = ARGV
raise "Expected installed recipe and version" unless ARGV.length == 2
formula = Formulary.factory(Pathname.new(recipe), :stable)
raise "Installed recipe version differs" unless formula.pkg_version.to_s == expected_version
stable = formula.stable
raise "Installed recipe has no stable source" unless stable

def source_record(identifier, resource)
  checksum = resource.checksum&.hexdigest
  {
    "SPDXID" => identifier,
    "downloadLocation" => resource.url,
    "licenseConcluded" => "NOASSERTION",
    "checksums" => checksum ? [{ "algorithm" => "SHA256", "checksumValue" => checksum }] : [],
  }
end

records = [source_record("SPDXRef-Archive-#{formula.name}-src", stable)]
stable.resources.each do |name, resource|
  records << source_record("SPDXRef-Resource-#{formula.name}-#{name}", resource)
end
stable.patches.each_with_index do |patch, index|
  # Embedded patches remain in the retained original recipe. External patches
  # must additionally retain their checksum-verified downloaded bytes.
  next unless patch.external?

  records << source_record("SPDXRef-Patch-#{formula.name}-#{index}", patch.resource)
end
puts JSON.generate({ "formula" => formula.name, "version" => formula.pkg_version.to_s,
                     "packages" => records, "origin" => "installed-keg-recipe" })
