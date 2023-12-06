"""
This script allows you to create a overlay network whilst adding two sub-interfaces as terminations.
"""

# Global Imports
from django.utils.text import slugify
from datetime import datetime

# Netbox Imports
from dcim.models import Device, Interface
from ipam.models import L2VPN, L2VPNTermination
from tenancy.models import Tenant
from extras.scripts import Script, ChoiceVar, IntegerVar, ObjectVar, StringVar

"""
Definition of script.
"""
class NewOverlay(Script):
    class Meta:
        name = "New Overlay"
        description = "Create a overlay and add two sub-interfaces."

    """
    Request variables as input.
    """
    vni_id = IntegerVar(
        label="VNI ID",
        required=True
    )
    
    tenant = ObjectVar(
        label="Tenant",
        model=Tenant,
        required=True
    )

    contract_product_choices = (
        ('IXP-Access - NL-ix', 'IXP-Access - NL-ix'),
        ('IXP-Access - KleyReX', 'IXP-Access - KleyReX'),
        ('IXP-Access - LocIX', 'IXP-Access - LocIX'),
        ('IP-Transit - RETN', 'IP-Transit - RETN'),
        ('L2-Transport', 'L2-Transport')
    )
    contract_product = ChoiceVar(
        label="Product",
        required=True,
        choices=contract_product_choices
    )

    contract_bandwidth_choices = (
        ('0M', '0M'),
        ('100M', '100M'),
        ('250M', '250M'),
        ('500M', '500M'),
        ('1G', '1G'),
        ('10G', '10G'),
        ('40G', '40G'),
        ('100G', '100G')
    )
    contract_bandwidth = ChoiceVar(
        label="Bandwidth",
        required=True,
        choices=contract_bandwidth_choices
    )

    a_end_device = ObjectVar(
        label="A-End Device",
        model=Device,
        query_params={
            "status": "active",
            "role": "switch"
        },
        required=False
    )
    a_end_interface = ObjectVar(
        label="A-End Port",
        model=Interface,
        query_params={
            "device_id": "$a_end_device",
            "type__n": "virtual"
        },
        required=False
    )
    a_end_vlan = IntegerVar(
        label="A-End VLAN",
        required=False
    )

    z_end_device = ObjectVar(
        label="Z-End Device",
        model=Device,
        query_params={
            "status": "active",
            "role": "switch"
        },
        required=False
    )
    z_end_interface = ObjectVar(
        label="Z-End Port",
        model=Interface,
        query_params={
            "device_id": "$z_end_device",
            "type__n": "virtual"
        },
        required=False
    )
    z_end_vlan = IntegerVar(
        label="Z-End VLAN",
        required=False
    )

    """
    Run the script and create the overlay.
    """
    def run(self, data, commit):
        # Create VNI
        vni = L2VPN(
            name="VNI" + str(data["vni_id"]),
            slug=slugify("VNI" + str(data["vni_id"])),
            identifier=data["vni_id"],
            type="vxlan-evpn",
            tenant=data["tenant"],
            description=(data["contract_product"] + " - " + data["contract_bandwidth"]),
            custom_field_data={
                "contract_product": data["contract_product"],
                "contract_bandwidth": data["contract_bandwidth"],
                "contract_start": datetime.today().strftime("%Y-%m-%d")
            }
        )
        vni.save()
        self.log_success(f"Created new VNI: {vni}")

        # Check if A-End is set and add termination.
        if data["a_end_device"] and data["a_end_interface"] and data["a_end_vlan"]:
            # Check if child-interface exists.
            childInterface = None
            childInterfaces = Interface.objects.filter(device=data["a_end_device"], parent=data["a_end_interface"])
            for interface in childInterfaces:
                if interface.name == (data["a_end_interface"].name + "." + str(data["a_end_vlan"])):
                    childInterface = interface
                    self.log_success(f"A-End Child-Interface already exists: {interface}")
            
            # Create child-interface if it does not exist.
            if childInterface == None:
                childInterface = Interface(
                    name=data["a_end_interface"].name + "." + str(data["a_end_vlan"]),
                    device=data["a_end_device"],
                    type="virtual",
                    parent=data["a_end_interface"],
                    description="VNI" + str(data["vni_id"])
                )
                childInterface.save()
                
                # Check if child-interface exists afterwards.
                if childInterface:
                    self.log_success(f"A-End Child-Interface is created: {childInterface}")
                else:
                    self.log_success("A-End Child-Interface could not be created!")

            # Add termination between VNI and child-interface.
            if childInterface != None:
                vniTermination = L2VPNTermination(
                    l2vpn=vni,
                    assigned_object=childInterface
                )
                vniTermination.save()

                # Check if termination exists.
                if vniTermination:
                    self.log_success(f"A-End L2VPN Termination is created: {vniTermination}")
                else:
                    self.log_success("A-End L2VPN Termination could not be created!")
            
        # Check if Z-End is set and add termination.
        if data["z_end_device"] and data["z_end_interface"] and data["z_end_vlan"]:
            # Check if child-interface exists.
            childInterface = None
            childInterfaces = Interface.objects.filter(device=data["z_end_device"], parent=data["z_end_interface"])
            for interface in childInterfaces:
                if interface.name == (data["z_end_interface"].name + "." + str(data["z_end_vlan"])):
                    childInterface = interface
                    self.log_success(f"Z-End Child-Interface already exists: {interface}")
            
            # Create child-interface if it does not exist.
            if childInterface == None:
                childInterface = Interface(
                    name=data["z_end_interface"].name + "." + str(data["z_end_vlan"]),
                    device=data["z_end_device"],
                    type="virtual",
                    parent=data["z_end_interface"],
                    description="VNI" + str(data["vni_id"])
                )
                childInterface.save()
                
                # Check if child-interface exists afterwards.
                if childInterface:
                    self.log_success(f"Z-End Child-Interface is created: {childInterface}")
                else:
                    self.log_success("Z-End Child-Interface could not be created!")

            # Add termination between VNI and child-interface.
            if childInterface != None:
                vniTermination = L2VPNTermination(
                    l2vpn=vni,
                    assigned_object=childInterface
                )
                vniTermination.save()

                # Check if termination exists.
                if vniTermination:
                    self.log_success(f"Z-End L2VPN Termination is created: {vniTermination}")
                else:
                    self.log_success("Z-End L2VPN Termination could not be created!")

        return False