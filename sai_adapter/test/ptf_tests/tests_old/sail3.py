# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Thrift SAI interface L3 tests
"""
import socket
import sys
import time
from struct import pack, unpack

from switch import *

import sai_base_test
from ptf.mask import Mask

@group('l3')
class L3IPv4HostTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending packet port 1 -> port 2 (192.168.0.1 -> 10.10.10.1 [id = 105])"
        switch_init2(self.client)
        port0 = port_list[0]
        port1 = port_list[1]
        v4_enabled = 1
        v6_enabled = 0
        mac_valid = 0
        mac = ''
        vlan_id0 = 10
        vlan_id1 = 15
        dmac1 = '00:11:22:33:44:55'

        bridge_port0 = br_port_list[port0]
        bridge_port1 = br_port_list[port1]

        attr_value = sai_thrift_attribute_value_t(u16=vlan_id0)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port0, attr)
        attr_value = sai_thrift_attribute_value_t(u16=vlan_id1)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)

        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id0)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid0 = self.client.sai_thrift_create_vlan([vlan_attr])
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id1)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid1 = self.client.sai_thrift_create_vlan([vlan_attr])

        tagging_mode = SAI_VLAN_TAGGING_MODE_UNTAGGED
        vlan_member0 = sai_thrift_create_vlan_member(self.client, vlan_oid0, bridge_port0, tagging_mode)
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid1, bridge_port1, tagging_mode)
        # mac_action = SAI_PACKET_ACTION_FORWARD
        # fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        # bridge_type = SAI_BRIDGE_TYPE_1Q
        # sai_thrift_create_fdb(self.client, dmac1, bridge_type, vlan_id1, None, bridge_port1, mac_action, fdb_entry_type)

        vr_id = sai_thrift_create_virtual_router(self.client, v4_enabled, v6_enabled)

        rif_id0 = sai_thrift_create_router_interface(self.client, vr_id, 0, 0, vlan_id0, v4_enabled, v6_enabled, mac)
        rif_id1 = sai_thrift_create_router_interface(self.client, vr_id, 0, 0, vlan_id1, v4_enabled, v6_enabled, mac)

        addr_family = SAI_IP_ADDR_FAMILY_IPV4
        ip_addr1 = '10.10.10.1'
        ip_addr1_subnet = '10.10.10.0'
        ip_mask1 = '255.255.255.0'
        sai_thrift_create_neighbor(self.client, addr_family, rif_id1, ip_addr1, dmac1)
        nhop1 = sai_thrift_create_nhop(self.client, addr_family, ip_addr1, rif_id1)
        sai_thrift_create_route(self.client, vr_id, addr_family, ip_addr1_subnet, ip_mask1, nhop1)

        # send the test packet(s)
        pkt = simple_tcp_packet(eth_dst=router_mac,
                                eth_src='00:22:22:22:22:55',
                                ip_dst='10.10.10.1',
                                ip_src='192.168.0.1',
                                ip_id=105,
                                ip_ttl=64)
        exp_pkt = simple_tcp_packet(eth_dst=dmac1,
                                eth_src=router_mac,
                                ip_dst='10.10.10.1',
                                ip_src='192.168.0.1',
                                ip_id=105,
                                ip_ttl=63)
        try:
            send_packet(self, 0, str(pkt))
            verify_packets(self, exp_pkt, [1])
        finally:
            sai_thrift_remove_route(self.client, vr_id, addr_family, ip_addr1_subnet, ip_mask1, rif_id1)
            self.client.sai_thrift_remove_next_hop(nhop1)
            sai_thrift_remove_neighbor(self.client, addr_family, rif_id1, ip_addr1, dmac1)
            self.client.sai_thrift_remove_router_interface(rif_id0)
            self.client.sai_thrift_remove_router_interface(rif_id1)
            
            # sai_thrift_delete_fdb(self.client, dmac1, vlan_id1, bridge_type, None)
            sai_thrift_flush_fdb_by_vlan(self.client, vlan_id0)
            sai_thrift_flush_fdb_by_vlan(self.client, 1)
            self.client.sai_thrift_remove_vlan_member(vlan_member0)
            self.client.sai_thrift_remove_vlan_member(vlan_member1)
            self.client.sai_thrift_remove_vlan(vlan_oid0)
            self.client.sai_thrift_remove_vlan(vlan_oid1)
            self.client.sai_thrift_remove_virtual_router(vr_id)
            attr_value = sai_thrift_attribute_value_t(u16=1)
            attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
            self.client.sai_thrift_set_port_attribute(port0, attr)
            self.client.sai_thrift_set_port_attribute(port1, attr)

@group('l3')
class ArpTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending arp packet to port 1"
        default_bridge, default_vlan_oid = switch_init2(self.client)
        # port1 = port_list[1]
        src_mac = '00:11:22:33:44:55'
        src_ip = '192.168.50.50'
        dst_ip = '192.168.45.45'
        hostif = sai_thrift_create_hostif(client=self.client,
                                          obj_id=default_vlan_oid,
                                          intf_name="vlan1")
        trap_group = sai_thrift_create_hostif_trap_group(self.client, 0, 0)
        trap1 = sai_thrift_create_hostif_trap(client=self.client,
                                              trap_type=SAI_HOSTIF_TRAP_TYPE_ARP_REQUEST,
                                              packet_action=SAI_PACKET_ACTION_TRAP,
                                              trap_group=trap_group)

        hostif_table = sai_thrift_create_hostif_table_entry(client=self.client,
                                             trap_id=trap1,
                                             channel_type=SAI_HOSTIF_TABLE_ENTRY_CHANNEL_TYPE_NETDEV_L3)
        
        # send the test packet(s)
        pkt = simple_arp_packet(eth_dst='ff:ff:ff:ff:ff:ff',
                                   eth_src=src_mac,
                                   arp_op=1,
                                   ip_snd=src_ip,
                                   ip_tgt=dst_ip,
                                   hw_snd=src_mac,
                                   hw_tgt='ff:ff:ff:ff:ff:ff')

        try:
        	send_packet(self, 1, str(pkt))
        	time.sleep(1)
            # verify_packets(self, exp_pkt, [1])
        finally:
            self.client.sai_thrift_remove_hostif_table_entry(hostif_table)
            self.client.sai_thrift_remove_hostif(hostif)
            self.client.sai_thrift_remove_hostif_trap(trap1)
            self.client.sai_thrift_remove_hostif_trap_group(trap_group)