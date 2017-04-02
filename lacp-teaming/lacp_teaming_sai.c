#include <assert.h>
#include <inttypes.h>
#include <sai.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char* test_profile_get_value(_In_ sai_switch_profile_id_t profile_id,
                                   _In_ const char* variable) {
  // UNREFERENCED_PARAMETER(profile_id);

  if (!strcmp(variable, "SAI_KEY_INIT_CONFIG_FILE")) {
    return "/usr/share/sai_2410.xml";
  } else if (!strcmp(variable, "KV_DEVICE_MAC_ADDRESS")) {
    return "20:03:04:05:06:00";
  } else if (!strcmp(variable, "SAI_KEY_L3_ROUTE_TABLE_SIZE")) {
    // return "1000";
  } else if (!strcmp(variable, "SAI_KEY_L3_NEIGHBOR_TABLE_SIZE")) {
    // return "2000";
  }

  return NULL;
}

/* Enumerate all the K/V pairs in a profile.
Pointer to NULL passed as variable restarts enumeration.
Function returns 0 if next value exists, -1 at the end of the list. */
int test_profile_get_next_value(_In_ sai_switch_profile_id_t profile_id,
                                _Out_ const char** variable,
                                _Out_ const char** value) {
  // UNREFERENCED_PARAMETER(profile_id);
  // UNREFERENCED_PARAMETER(variable);
  // UNREFERENCED_PARAMETER(value);

  return -1;
}

const service_method_table_t test_services = {test_profile_get_value,
                                              test_profile_get_next_value};

/* Enumerate all the K/V pairs in a profile.
Pointer to NULL passed as variable restarts enumeration.
Function returns 0 if next value exists, -1 at the end of the list. */

int main(int argc, char** argv) {
  sai_hostif_api_t* hostif_api;

  sai_api_initialize(0, &test_services);
  sai_api_query(SAI_API_HOSTIF, (void**)&hostif_api);
  sai_object_id_t switch_id = 0;
  sai_object_id_t port_id[2];
  port_id[0] = 0;
  port_id[1] = 2;  // TODO

  // create trap group (currently only 1.)
  sai_object_id_t prio_group;

  sai_attribute_t sai_attr_list[2];
  // sai_attr_list[0].id = SAI_HOSTIF_TRAP_GROUP_ATTR_PRIO;
  // sai_attr_list[0].value = 7;
  sai_attr_list[0].id = SAI_HOSTIF_TRAP_GROUP_ATTR_QUEUE;
  sai_attr_list[0].value.u32 = 0;  // high_queue_id; // high_queue_id is a queue
                                   // element created via QoS SAI API
  sai_attr_list[1].id = SAI_HOSTIF_TRAP_GROUP_ATTR_POLICER;
  sai_attr_list[1].value.oid = 0;  // high_policer_id; //high_policer_id is a
                                   // policer element created via policer SAI
                                   // API
  hostif_api->create_hostif_trap_group(&prio_group, switch_id, 2,
                                       sai_attr_list);

  // Create host interface channel
  sai_object_id_t host_if_id[2];
  sai_attribute_t sai_if_channel_attr[3];
  sai_if_channel_attr[0].id = SAI_HOSTIF_ATTR_TYPE;
  sai_if_channel_attr[0].value.s32 = SAI_HOSTIF_TYPE_NETDEV;
  sai_if_channel_attr[1].id = SAI_HOSTIF_ATTR_OBJ_ID;
  sai_if_channel_attr[1].value.oid =
      port_id[0];  // port_id is a port element created via port SAI API
  sai_if_channel_attr[2].id = SAI_HOSTIF_ATTR_NAME;
  strcpy(sai_if_channel_attr[2].value.chardata,"port1");
  hostif_api->create_hostif(&host_if_id[0], switch_id, 3, sai_if_channel_attr);
  sai_if_channel_attr[0].id = SAI_HOSTIF_ATTR_TYPE;
  sai_if_channel_attr[0].value.s32 = SAI_HOSTIF_TYPE_NETDEV;
  sai_if_channel_attr[1].id = SAI_HOSTIF_ATTR_OBJ_ID;
  sai_if_channel_attr[1].value.oid =
      port_id[1];  // port_id is a port element created via port SAI API
  sai_if_channel_attr[2].id = SAI_HOSTIF_ATTR_NAME;
  strcpy(sai_if_channel_attr[2].value.chardata,"port2");
  hostif_api->create_hostif(&host_if_id[1], switch_id, 3, sai_if_channel_attr);

  // Configuring Trap-IDs
  sai_attribute_t sai_trap_attr[3];
  sai_object_id_t host_trap_id[1];
  // configure LACP trap_id
  sai_trap_attr[0].id = SAI_HOSTIF_TRAP_ATTR_TRAP_GROUP;
  sai_trap_attr[0].value.oid = prio_group;
  sai_trap_attr[1].id = SAI_HOSTIF_TRAP_ATTR_PACKET_ACTION;
  sai_trap_attr[1].value.s32 = SAI_PACKET_ACTION_TRAP;
  sai_trap_attr[2].id = SAI_HOSTIF_TRAP_ATTR_TRAP_TYPE;
  sai_trap_attr[2].value.s32 = SAI_HOSTIF_TRAP_TYPE_LACP;
  hostif_api->create_hostif_trap(&host_trap_id[0], switch_id, 3, sai_trap_attr);

  // Configuring Host tables
  sai_object_id_t host_table_entry[1];
  sai_if_channel_attr[0].id = SAI_HOSTIF_TABLE_ENTRY_ATTR_TYPE;
  sai_if_channel_attr[0].value.s32 = SAI_HOSTIF_TABLE_ENTRY_TYPE_TRAP_ID;
  sai_if_channel_attr[1].id = SAI_HOSTIF_TABLE_ENTRY_ATTR_TRAP_ID;
  sai_if_channel_attr[1].value.oid = host_trap_id[1];
  sai_if_channel_attr[2].id = SAI_HOSTIF_TABLE_ENTRY_ATTR_CHANNEL_TYPE;
  sai_if_channel_attr[2].value.s32 =
      SAI_HOSTIF_TABLE_ENTRY_CHANNEL_TYPE_NETDEV_PHYSICAL_PORT;
  hostif_api->create_hostif_table_entry(&host_table_entry[0], switch_id, 3,
                                        sai_if_channel_attr);

  sai_api_uninitialize();
}
