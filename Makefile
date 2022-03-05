
DESTDIR ?= /usr/local

install:
	install -m 0755 lsmount $(DESTDIR)/bin/
	install -m 0755 df-dir $(DESTDIR)/bin/
