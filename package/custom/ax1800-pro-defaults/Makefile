include $(TOPDIR)/rules.mk
PKG_NAME:=ax1800-pro-defaults
PKG_RELEASE:=2
PKG_LICENSE:=MIT
include $(INCLUDE_DIR)/package.mk

define Package/ax1800-pro-defaults
  SECTION:=base
  CATEGORY:=Base system
  TITLE:=Credential-free AX1800 Pro defaults
  DEPENDS:=@TARGET_qualcommax_ipq60xx +fish +wpad-openssl +firewall4
  PKGARCH:=all
endef
define Build/Compile
endef
define Package/ax1800-pro-defaults/install
	$(INSTALL_DIR) $(1)/etc/uci-defaults $(1)/lib/upgrade/keep.d
	$(INSTALL_BIN) ./files/99-zz-ax1800-pro $(1)/etc/uci-defaults/
	$(INSTALL_DATA) ./files/keep $(1)/lib/upgrade/keep.d/ax1800-pro
endef
$(eval $(call BuildPackage,ax1800-pro-defaults))
