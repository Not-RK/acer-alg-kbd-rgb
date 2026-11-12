KVER ?= $(shell uname -r)
KDIR ?= /lib/modules/$(KVER)/build
MDIR := $(CURDIR)

.PHONY: all install clean

all:
	$(MAKE) -C $(KDIR) M=$(MDIR) modules

install: all
	$(MAKE) -C $(KDIR) M=$(MDIR) modules_install
	depmod -a $(KVER)

clean:
	$(MAKE) -C $(KDIR) M=$(MDIR) clean
