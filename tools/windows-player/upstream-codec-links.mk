# Exact current release dependency files force relinking when an archive changes.
upstream_codec_libdir = /work/upstream-codecs-1.1.1/prefix/lib
upstream_codec_maps = /work/upstream-codecs-1.1.1/link-maps
upstream_codec_recipe := $(lastword $(MAKEFILE_LIST))
# Automake has already expanded its *_DEPENDENCIES into target prerequisites
# before this second makefile is read. Add real target prerequisites here.
libmpg123_plugin.la: $(upstream_codec_libdir)/libmpg123.a $(upstream_codec_recipe)
libzvbi_plugin.la: $(upstream_codec_libdir)/libzvbi.a $(upstream_codec_recipe)
libaom_plugin.la: $(upstream_codec_libdir)/libaom.a $(upstream_codec_recipe)
libmad_plugin.la: $(upstream_codec_libdir)/libmad.a $(upstream_codec_recipe)
# Qt is built explicitly by build-player.sh. Build the flat module graph in
# this make process: recursive "all" discards the extra -f makefile arguments.
all-am: $(BUILT_SOURCES)
# Every generated LINK variant consumes LDFLAGS. MAD uses generic LINK and
# ignores libmad_plugin_la_LDFLAGS, unlike the three per-target link recipes.
libmpg123_plugin.la: LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/mpg123.map
libzvbi_plugin.la: LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/zvbi.map
libaom_plugin.la: LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/aom.map
libmad_plugin.la: LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/mad.map
# libmad's configure probe uses --with-mad; the link itself also binds the archive.
MAD_LIBS = $(upstream_codec_libdir)/libmad.a
