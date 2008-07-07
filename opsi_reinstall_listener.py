# -*- coding: utf-8 -*-

"""
   = = = = = = = = = = = = = = = = = = = = = = =
   =       OPSI reinstallation listener        =
   = = = = = = = = = = = = = = = = = = = = = = =
   
   @copyright:	uib - http://www.uib.de - <info@uib.de>
   @author: Jan Schneider <j.schneider@uib.de>
   @license: GNU GPL, see COPYING for details.
"""

__version__ = "0.9.1"

name='opsi_reinstall_listener'
description='Reinstallation listener for opsi'
filter='(objectClass=univentionWindows)'
attributes=['univentionWindowsReinstall']

BOOTIMAGE = 'install'

import listener
import os, re, ldap, string, univention.debug

from OPSI.Logger import *
from OPSI.Backend.BackendManager import BackendManager, logger

logger.setUniventionLogger(univention.debug)
logger.setUniventionClass(univention.debug.LISTENER)


def handler(dn, new, old):
	
	if not new:
		return
	
	reinst = new.get('univentionWindowsReinstall')
	if not reinst:
		return
	
	listener.setuid(0)
	
	bm = None
	try:
		bm = BackendManager( authRequired = False )
	except Exception, e:
		logger.error('Failed to create BackendManager instance: %s' % e)
		return
	
	hostId = ''
	try:
		hostId = bm.getHostId(dn)
		logger.info('DN: %s, hostId: %s' % (dn, hostId))
	except Exception, e:
		logger.error('Failed to get hostId: %s, trying to create host' % e)
		hostName = ''
		domain = ''
		parts = dn.split(',')
		for i in range(len(parts)):
			(att, val) = parts[i].strip().split('=', 1)
			if (i==0):
				hostName = val
			elif(att.lower() == 'dn'):
				if domain: domain += '.'
				domain += val
			
		hostId = bm.createClient( hostName, domain )
		logger.notice("Host '%s' created (dn=%s)" % (hostId, dn))
		
	netbootProducts = bm.getInstallableNetBootProductIds_list(hostId)
	productIds = []
	try:
		for actionRequest in bm.getProductActionRequests_listOfHashes(hostId):
			if actionRequest.get('productId') not in netbootProducts:
				continue
			if not actionRequest.get('actionRequest').startswith('setup'):
				continue
			productIds.append(actionRequest.get('productId'))
	except Exception, e:
		logger.warning("Failed to get product action requests for client '%s': %s'" % (hostId, e))
	if not productIds:
		logger.warning("Action request 'setup' not set for any netboot product, client '%s'" % hostId)
	
	if ( reinst[0] == '0'):
		for productId in productIds:
			logger.notice("Unsetting action for client '%s', product '%s'" % (hostId, productId))
		
			try:
				bm.unsetProductActionRequest(productId, hostId)
			except Exception, e:
				logger.warning("Failed to unset product action request for client '%s', product '%s': %s'" % (hostId, productId, e))
	
	elif ( reinst[0] == '1'):
		#try:
		#	bm.createClient( hostId.split('.')[0], '.'.join( hostId.split('.')[1:] ) )
		#except Exception, e:
		#	e = str(e)
		#	if (e.find("already exists") == -1):
		#		logger.error("Failed to create client '%s': %s'" % (hostId, e))
		
		productId = ''
		if productIds:
			productId = productIds[0]
		else:
			# Get netboot product from installation status
			productIds = []
			for installationStatus in bm.getProductInstallationStatus_listOfHashes(hostId):
				if installationStatus.get('productId') not in netbootProducts:
					continue
				if installationStatus.get('actionRequest') not in ['installed']:
					continue
				productIds.append(installationStatus.get('productId'))
			
			if (len(productIds) > 0):
				if (len(productIds) > 1):
					logger.warning("More than one netboot product is installed: %s, client '%s', using '%s'" \
							% (', '.join(productIds), hostId, productIds[0]) )
				productId = productIds[0]
			else:
				logger.info("Installation status 'installed' not set for any netboot product, client '%s'" % hostId)
			
		if not productId:
			# Get default netboot product
			try:
				productId = bm.getDefaultNetBootProductId(hostId)
			except Exception, e:
				logger.warning(e)
			
		if not productId:
			logger.error("Failed to set PXE boot configuration for host '%s': failed to get default netboot product" % hostId)
			productId = bm.unsetPXEBootConfiguration(hostId)
			bm.exit()
			return
		
		logger.notice("Setting product action request 'setup' for client '%s', product '%s'" % (hostId, productId) )
		
		try:
			bm.setProductActionRequest(productId, hostId, 'setup')
		except Exception, e:
			logger.error("Failed to set action request 'setup' for client '%s', product '%s': %s'" % (hostId, productId, e))
			productId = bm.unsetPXEBootConfiguration(hostId)
	
	bm.exit()
	
