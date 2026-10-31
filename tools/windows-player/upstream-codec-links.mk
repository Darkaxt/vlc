# Exact current release dependency files force relinking when an archive changes.
upstream_codec_libdir = /work/upstream-codecs-1.1.1/prefix/lib
upstream_codec_maps = /work/upstream-codecs-1.1.1/link-maps
libmpg123_plugin_la_DEPENDENCIES += $(upstream_codec_libdir)/libmpg123.a
libzvbi_plugin_la_DEPENDENCIES += $(upstream_codec_libdir)/libzvbi.a
libaom_plugin_la_DEPENDENCIES += $(upstream_codec_libdir)/libaom.a
libmad_plugin_la_DEPENDENCIES += $(upstream_codec_libdir)/libmad.a
libmpg123_plugin_la_LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/mpg123.map
libzvbi_plugin_la_LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/zvbi.map
libaom_plugin_la_LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/aom.map
libmad_plugin_la_LDFLAGS += -Wl,-Map,$(upstream_codec_maps)/mad.map
# libmad's configure probe uses --with-mad; the link itself also binds the archive.
MAD_LIBS = $(upstream_codec_libdir)/libmad.a
