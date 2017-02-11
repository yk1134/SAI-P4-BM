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
Thrift SAI interface L2 tests
"""
import socket
from switch import *
import sai_base_test
import sys
sys.path.append('../sai_thrift_src/gen-py/')
from switch_sai.ttypes import *
import random
from sai_types import *

@group('l2')
class L2AcceptedFrameType(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        vlan_id = 1
        hw_port1 = 0
        hw_port2 = 1

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]
        
        # port2 drops tagged. port1 drops untagged
        attr_value = sai_thrift_attribute_value_t(booldata=True)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_DROP_UNTAGGED, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_DROP_TAGGED, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port2, attr)

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, default_bridge_type, vlan_id, default_bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, default_bridge_type, vlan_id, default_bridge, bridge_port2, mac_action, fdb_entry_type)
        
        untagged_pkt1 = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                          eth_src='00:11:11:11:11:11',
                                          ip_dst='10.0.0.1',
                                          ip_id=101,
                                          ip_ttl=64)
        tagged_pkt1 = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                        eth_src='00:11:11:11:11:11',
                                        ip_dst='10.0.0.1',
                                        ip_id=101,
                                        dl_vlan_enable=True,
                                        vlan_vid=vlan_id,
                                        ip_ttl=64,
                                        pktlen=104)
        untagged_pkt2 = simple_tcp_packet(eth_dst='00:11:11:11:11:11',
                                          eth_src='00:22:22:22:22:22',
                                          ip_dst='10.0.0.1',
                                          ip_id=101,
                                          ip_ttl=64)
        tagged_pkt2 = simple_tcp_packet(eth_dst='00:11:11:11:11:11',
                                        eth_src='00:22:22:22:22:22',
                                        ip_dst='10.0.0.1',
                                        ip_id=101,
                                        dl_vlan_enable=True,
                                        vlan_vid=vlan_id,
                                        ip_ttl=64,
                                        pktlen=104)

        try:
            print "Sending tagged packet port 0 -> port 1"
            send_packet(self, hw_port1, str(tagged_pkt1))
            verify_packets(self, tagged_pkt1, [hw_port2])
            print "Sending tagged packet port 1 -> port 0"
            send_packet(self, hw_port2, str(tagged_pkt2))
            verify_no_packet_any(self, tagged_pkt2, port_list.keys())
            print "Sending untagged packet port 0 -> port 1"
            send_packet(self, hw_port1, str(untagged_pkt1))
            verify_no_packet_any(self, untagged_pkt1, port_list.keys())
            print "Sending untagged packet port 1 -> port 0"
            send_packet(self, hw_port2, str(untagged_pkt2))
            verify_packets(self, untagged_pkt2, [hw_port1])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, default_bridge)
            sai_thrift_delete_fdb(self.client, mac2, default_bridge)
            attr_value = sai_thrift_attribute_value_t(booldata=False)
            attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_DROP_UNTAGGED, value=attr_value) 
            self.client.sai_thrift_set_port_attribute(port1, attr)
            attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_DROP_TAGGED, value=attr_value) 
            self.client.sai_thrift_set_port_attribute(port2, attr)
 
@group('l2')
class L21DBridgeBasicTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending L2 packet port 0 -> port 1"
        vlan_id = 10
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        hw_port1 = 0
        hw_port2 = 1
        
        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]
        
        bind_mode = SAI_PORT_BIND_MODE_SUB_PORT
        self.client.sai_thrift_remove_port(port1)
        self.client.sai_thrift_remove_port(port2)
        port1 = sai_thrift_create_port(self.client, bind_mode, hw_port1, vlan_id)
        port2 = sai_thrift_create_port(self.client, bind_mode, hw_port2, vlan_id)

        # Create 1D Bridge
        bridge_type = SAI_BRIDGE_TYPE_1D
        bridge_attr_value = sai_thrift_attribute_value_t(s32=bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_SUB_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port2, vlan_id, bridge)

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)

        pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64)

        try:
            send_packet(self, hw_port1, str(pkt))
            verify_packets(self, pkt, [hw_port2])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            bind_mode = SAI_PORT_BIND_MODE_PORT
            vlan_id = 1
            attr_value = sai_thrift_attribute_value_t(s32=bind_mode)
            attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_BIND_MODE, value=attr_value)
            self.client.sai_thrift_set_port_attribute(port1, attr)
            self.client.sai_thrift_set_port_attribute(port2, attr)
            attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
            attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value)
            self.client.sai_thrift_set_port_attribute(port1, attr)
            self.client.sai_thrift_set_port_attribute(port2, attr)

@group('l2')
class L21QBridgeAccess2AccessTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending L2 packet port 0 -> port 1"
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        vlan_id = 10

        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]

        attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)
        self.client.sai_thrift_set_port_attribute(port2, attr)

        # Create 1Q Bridge
        bridge_type = SAI_BRIDGE_TYPE_1Q
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port2, vlan_id, bridge)

        # Create VLAN
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid = self.client.sai_thrift_create_vlan([vlan_attr])

        # tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        tagging_mode = SAI_VLAN_TAGGING_MODE_UNTAGGED
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port1, tagging_mode)
        vlan_member2 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port2, tagging_mode)
        # SAI_VLAN_ATTR_MEMBER_LIST

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)
        
        pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64)

        try:
            send_packet(self, hw_port1, str(pkt))
            verify_packets(self, pkt, [hw_port2])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_vlan_member(vlan_member1)
            self.client.sai_thrift_remove_vlan_member(vlan_member2)
            self.client.sai_thrift_delete_vlan(vlan_oid)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_port(port1)
            self.client.sai_thrift_remove_port(port2)

@group('l2') 
class L21QBridgeAccess2TrunkTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        # switch_init(self.client)
        vlan_id = 11
        trunk_pvid = 20
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        self.client.sai_thrift_create_switch([])

        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1
        print "Sending L2 packet Access(%d) -> Trunk(%d) (trunk vlan=%d)" % (hw_port1, hw_port2, vlan_id)

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]

        attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)
        self.client.sai_thrift_set_port_attribute(port2, attr)

        # Create 1Q Bridge
        bridge_type = SAI_BRIDGE_TYPE_1Q
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port2, vlan_id, bridge)

        # Create VLAN
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid = self.client.sai_thrift_create_vlan([vlan_attr])

        # tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        tagging_mode = SAI_VLAN_TAGGING_MODE_UNTAGGED
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port1, tagging_mode)
        tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        vlan_member2 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port2, tagging_mode)
        # SAI_VLAN_ATTR_MEMBER_LIST

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)
        
        pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64)
        exp_pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                dl_vlan_enable=True,
                                vlan_vid=vlan_id,
                                ip_ttl=64,
                                pktlen=104)
        try:
            send_packet(self, hw_port1, str(pkt))
            verify_packets(self, exp_pkt, [hw_port2])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_vlan_member(vlan_member1)
            self.client.sai_thrift_remove_vlan_member(vlan_member2)
            self.client.sai_thrift_delete_vlan(vlan_oid)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_port(port1)
            self.client.sai_thrift_remove_port(port2)


@group('l2')
class L21QBridgeTrunk2TrunkTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        # switch_init(self.client)
        vlan_id = 12
        trunk_pvid = 20
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        self.client.sai_thrift_create_switch([])

        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1
        print "Sending L2 packet Trunk(%d) -> Trunk(%d) (trunk vlan=%d)" % (hw_port1, hw_port2, vlan_id)

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]

        attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)
        self.client.sai_thrift_set_port_attribute(port2, attr)

        # Create 1Q Bridge
        bridge_type = SAI_BRIDGE_TYPE_1Q
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port2, vlan_id, bridge)

        # Create VLAN
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid = self.client.sai_thrift_create_vlan([vlan_attr])

        tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port1, tagging_mode)
        vlan_member2 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port2, tagging_mode)
        # SAI_VLAN_ATTR_MEMBER_LIST

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)
        
        pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                dl_vlan_enable=True,
                                vlan_vid=vlan_id,
                                ip_ttl=64)
        exp_pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                dl_vlan_enable=True,
                                vlan_vid=vlan_id,
                                ip_ttl=64)
        try:
            send_packet(self, hw_port1, str(pkt))
            verify_packets(self, exp_pkt, [hw_port2])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_vlan_member(vlan_member1)
            self.client.sai_thrift_remove_vlan_member(vlan_member2)
            self.client.sai_thrift_delete_vlan(vlan_oid)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_port(port1)
            self.client.sai_thrift_remove_port(port2)

@group('l2')
class L21QBridgeTrunk2AccessTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        # switch_init(self.client)
        vlan_id = 13
        trunk_pvid = 20
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        self.client.sai_thrift_create_switch([])

        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1
        print "Sending L2 packet Trunk(%d) -> Access(%d) (trunk vlan=%d)" % (hw_port1, hw_port2, vlan_id)

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]

        attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value) 
        self.client.sai_thrift_set_port_attribute(port1, attr)
        self.client.sai_thrift_set_port_attribute(port2, attr)

        # Create 1Q Bridge
        bridge_type = SAI_BRIDGE_TYPE_1Q
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port2, vlan_id, bridge)

        # Create VLAN
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vlan_id)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid = self.client.sai_thrift_create_vlan([vlan_attr])

        tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port1, tagging_mode)
        tagging_mode = SAI_VLAN_TAGGING_MODE_UNTAGGED
        vlan_member2 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port2, tagging_mode)
        # SAI_VLAN_ATTR_MEMBER_LIST

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)
        
        pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                dl_vlan_enable=True,
                                vlan_vid=vlan_id,
                                ip_ttl=64)
        exp_pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                eth_src='00:11:11:11:11:11',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64,
                                pktlen=96)
        try:
            send_packet(self, hw_port1, str(pkt))
            verify_packets(self, exp_pkt, [hw_port2])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_vlan_member(vlan_member1)
            self.client.sai_thrift_remove_vlan_member(vlan_member2)
            self.client.sai_thrift_delete_vlan(vlan_oid)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_port(port1)
            self.client.sai_thrift_remove_port(port2)

@group('l2')
class L21DLagTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending 3 L2 (1D) Lag packets port 0 -> port 1/2/3"
        vlan_id = 15
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        self.client.sai_thrift_create_switch([])

        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1
        hw_port3 = 2
        hw_port4 = 3

        switch_init2(self.client)
        port1 = port_list[hw_port1]
        port2 = port_list[hw_port2]
        port3 = port_list[hw_port3]
        port4 = port_list[hw_port4]
        bridge_port1 = br_port_list[port1]
        bridge_port2 = br_port_list[port2]
        bridge_port3 = br_port_list[port3]
        bridge_port4 = br_port_list[port4]

        bind_mode = SAI_PORT_BIND_MODE_SUB_PORT
        self.client.sai_thrift_remove_port(port1)
        self.client.sai_thrift_remove_port(port2)
        self.client.sai_thrift_remove_port(port3)
        self.client.sai_thrift_remove_port(port4)
        port1 = sai_thrift_create_port(self.client, bind_mode, hw_port1, vlan_id)
        port2 = sai_thrift_create_port(self.client, bind_mode, hw_port2, vlan_id)
        port3 = sai_thrift_create_port(self.client, bind_mode, hw_port3, vlan_id)
        port4 = sai_thrift_create_port(self.client, bind_mode, hw_port4, vlan_id)

        # Create LAG
        lag = self.client.sai_thrift_create_lag([])
        lag_member1 = sai_thrift_create_lag_member(self.client, port4, lag)
        lag_member2 = sai_thrift_create_lag_member(self.client, port2, lag)
        lag_member3 = sai_thrift_create_lag_member(self.client, port3, lag)

        # Set LAG Vlan attr
        attr_value = sai_thrift_attribute_value_t(u16=vlan_id)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value)
        self.client.sai_thrift_set_port_attribute(lag, attr)

        # Create 1D Bridge
        bridge_type = SAI_BRIDGE_TYPE_1D
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_SUB_PORT
        self.client.sai_thrift_remove_bridge_port(bridge_port1)
        self.client.sai_thrift_remove_bridge_port(bridge_port2)
        self.client.sai_thrift_remove_bridge_port(bridge_port3)
        self.client.sai_thrift_remove_bridge_port(bridge_port4)
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vlan_id, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, lag, vlan_id, bridge)

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vlan_id, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vlan_id, bridge, bridge_port2, mac_action, fdb_entry_type)

        pkt = simple_tcp_packet(eth_dst='00:11:11:11:11:11',
                                eth_src='00:22:22:22:22:22',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64)
        try:
            send_packet(self, hw_port3, str(pkt))
            verify_packets(self, pkt, [hw_port1])
            for ip_id in [101,103,105]:
                pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                    eth_src='00:11:11:11:11:11',
                                    ip_dst='10.0.0.1',
                                    ip_id=ip_id,
                                    ip_ttl=64)
                send_packet(self, hw_port1, str(pkt))
                verify_packets_any(self, pkt, [hw_port2, hw_port3, hw_port4])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_lag_member(lag_member1)
            self.client.sai_thrift_remove_lag_member(lag_member2)
            self.client.sai_thrift_remove_lag_member(lag_member3)
            self.client.sai_thrift_remove_lag(lag)

@group('l2')
class L21QLagTest(sai_base_test.ThriftInterfaceDataPlane):
    def runTest(self):
        print
        print "Sending 3 L2 (1Q Access2Access) Lag packets port 0 -> port 1/2/3"
        vid = 15
        mac1 = '00:11:11:11:11:11'
        mac2 = '00:22:22:22:22:22'
        self.client.sai_thrift_create_switch([])
        # Set HW ports
        hw_port1 = 0
        hw_port2 = 1
        hw_port3 = 2
        hw_port4 = 3

        # Create Ports
        bind_mode = SAI_PORT_BIND_MODE_PORT
        port1 = sai_thrift_create_port(self.client, bind_mode, hw_port1, vid)
        port2 = sai_thrift_create_port(self.client, bind_mode, hw_port2)
        port3 = sai_thrift_create_port(self.client, bind_mode, hw_port3)
        port4 = sai_thrift_create_port(self.client, bind_mode, hw_port4)

        # Create LAG
        lag = self.client.sai_thrift_create_lag([])
        lag_member1 = sai_thrift_create_lag_member(self.client, port4, lag)
        lag_member2 = sai_thrift_create_lag_member(self.client, port2, lag)
        lag_member3 = sai_thrift_create_lag_member(self.client, port3, lag)

        # Set LAG Vlan attr
        attr_value = sai_thrift_attribute_value_t(u16=vid)
        attr = sai_thrift_attribute_t(id=SAI_PORT_ATTR_PORT_VLAN_ID, value=attr_value)
        self.client.sai_thrift_set_port_attribute(lag, attr)

        # Create 1Q Bridge
        bridge_type = SAI_BRIDGE_TYPE_1Q
        bridge_attr_value = sai_thrift_attribute_value_t(s32= bridge_type)
        bridge_attr = sai_thrift_attribute_t(id=SAI_BRIDGE_ATTR_TYPE, value=bridge_attr_value)
        bridge = self.client.sai_thrift_create_bridge([bridge_attr])

        # Create Bridge ports
        bridge_port_type = SAI_BRIDGE_PORT_TYPE_PORT
        bridge_port1 = sai_thrift_create_bridge_port(self.client, bridge_port_type, port1, vid, bridge)
        bridge_port2 = sai_thrift_create_bridge_port(self.client, bridge_port_type, lag, vid, bridge)
        
        # Create VLAN
        vlan_attr_value = sai_thrift_attribute_value_t(u16= vid)
        vlan_attr = sai_thrift_attribute_t(id=SAI_VLAN_ATTR_VLAN_ID, value=vlan_attr_value)
        vlan_oid = self.client.sai_thrift_create_vlan([vlan_attr])

        # tagging_mode = SAI_VLAN_TAGGING_MODE_TAGGED
        tagging_mode = SAI_VLAN_TAGGING_MODE_UNTAGGED
        vlan_member1 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port1, tagging_mode)
        vlan_member2 = sai_thrift_create_vlan_member(self.client, vlan_oid, bridge_port2, tagging_mode)

        # Create FDB Entries:
        mac_action = SAI_PACKET_ACTION_FORWARD
        fdb_entry_type = SAI_FDB_ENTRY_TYPE_STATIC
        sai_thrift_create_fdb(self.client, mac1, bridge_type, vid, bridge, bridge_port1, mac_action, fdb_entry_type)
        sai_thrift_create_fdb(self.client, mac2, bridge_type, vid, bridge, bridge_port2, mac_action, fdb_entry_type)

        pkt = simple_tcp_packet(eth_dst='00:11:11:11:11:11',
                                eth_src='00:22:22:22:22:22',
                                ip_dst='10.0.0.1',
                                ip_id=101,
                                ip_ttl=64)
        try:
            send_packet(self, hw_port3, str(pkt))
            verify_packets(self, pkt, [hw_port1])
            for ip_id in [101,103,105]:
                pkt = simple_tcp_packet(eth_dst='00:22:22:22:22:22',
                                    eth_src='00:11:11:11:11:11',
                                    ip_dst='10.0.0.1',
                                    ip_id=ip_id,
                                    ip_ttl=64)
                send_packet(self, hw_port1, str(pkt))
                verify_packets_any(self, pkt, [hw_port2, hw_port3, hw_port4])
        finally:
            sai_thrift_delete_fdb(self.client, mac1, bridge)
            sai_thrift_delete_fdb(self.client, mac2, bridge)
            self.client.sai_thrift_remove_bridge_port(bridge_port1)
            self.client.sai_thrift_remove_bridge_port(bridge_port2)
            self.client.sai_thrift_remove_bridge(bridge)
            self.client.sai_thrift_remove_lag_member(lag_member1)
            self.client.sai_thrift_remove_lag_member(lag_member2)
            self.client.sai_thrift_remove_lag_member(lag_member3)
            self.client.sai_thrift_remove_lag(lag)
            self.client.sai_thrift_remove_port(port1)
            self.client.sai_thrift_remove_port(port2)
            self.client.sai_thrift_remove_port(port3)
            self.client.sai_thrift_remove_port(port4)
