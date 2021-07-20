from opentrons import types
from opentrons_functions.transfer import add_buffer
from opentrons_functions.util import odd_or_even


def bead_mix(pipette,
             plate,
             cols,
             tiprack,
             n=5,
             z_offset=2,
             mix_vol=200,
             mix_lift=0,
             drop_tip=False):
    for col in cols:
        pipette.pick_up_tip(tiprack.wells_by_name()[col])
        pipette.mix(n,
                    mix_vol,
                    plate[col].bottom(z=z_offset))
        pipette.dispense(mix_vol,
        			plate[col].bottom(z=z_offset + mix_lift))
        			
        pipette.blow_out(plate[col].top())

        if drop_tip:
            pipette.drop_tip()
        else:
            pipette.return_tip()
    return()


def remove_supernatant(pipette,
                       plate,
                       cols,
                       tiprack,
                       waste,
                       super_vol=600,
                       tip_vol=200,
                       rate=0.25,
                       bottom_offset=2,
                       drop_tip=False):

    # remove supernatant

    for col in cols:
        vol_remaining = super_vol
        # transfers to remove supernatant:
        pipette.pick_up_tip(tiprack.wells_by_name()[col])
        while vol_remaining > 0:
            transfer_vol = min(vol_remaining, (tip_vol - 10))
            if vol_remaining <= 190:
                z_height = bottom_offset
            else:
                z_height = 4
            pipette.aspirate(transfer_vol,
                             plate[col].bottom(z=z_height),
                             rate=rate)
            pipette.air_gap(10)
            pipette.dispense(transfer_vol + 10, waste.top())
            vol_remaining -= transfer_vol#pipette.blow_out()
        # we're done with these tips at this point
        pipette.blow_out()
        if drop_tip:
            pipette.drop_tip()
        else:
            pipette.return_tip()
    return()


def bead_wash(  # global arguments
              protocol,
              magblock,
              pipette,
              plate,
              cols,
              # super arguments
              super_waste,
              super_tiprack,
              # wash buffer arguments
              source_wells,
              source_vol,
              # mix arguments
              mix_tiprack,
              # optional arguments
              resuspend_beads=True,
              super_vol=600,
              rate=0.25,
              super_bottom_offset=2,
              super_tip_vol=200,
              drop_super_tip=True,
              wash_vol=300,
              remaining=None,
              wash_tip=None,
              wash_tip_vol=300,
              drop_wash_tip=True,
              touch_wash_tip=True,
              mix_vol=200,
              mix_n=10,
              mix_z_offset=2,
              mix_lift=0,
              drop_mix_tip=False,
              mag_engage_height=None,
              pause_s=300):
    # Wash

    # This should:
    # - pick up tip from position 7
    # - pick up 190 µL from the mag plate
    # - air gap
    # - dispense into position 11
    # - repeat x
    # - trash tip
    # - move to next column
    # - disengage magnet

    # remove supernatant
    remove_supernatant(pipette,
                       plate,
                       cols,
                       super_tiprack,
                       super_waste,
                       tip_vol=super_tip_vol,
                       super_vol=super_vol,
                       rate=rate,
                       bottom_offset=super_bottom_offset,
                       drop_tip=drop_super_tip)
	
	if resuspend_beads:
    	# disengage magnet
    	magblock.disengage()

    # This should:
    # - Pick up tips from column 3 of location 2
    # - pick up isopropanol from position 5 column 3
    # - dispense to `cols` in mag plate
    # - pick up isopropanol from position 5 column 4
    # - dispense to `cols` in mag plate
    # - drop tips at end

    # add wash -- changed from add isopropanol
    wash_wells, wash_remaining = add_buffer(pipette,
                                            source_wells,
                                            plate,
                                            cols,
                                            wash_vol,
                                            source_vol,
                                            tip=wash_tip,
                                            tip_vol=wash_tip_vol,
                                            remaining=remaining,
                                            drop_tip=drop_wash_tip,
                                            touch_tip=touch_wash_tip)

    # This should:
    # - grab a tip from position 8
    # - mix 5 times the corresponding well on mag plate
    # - blow out
    # - return tip
    # - do next col
    # - engage magnet
	
	if resuspend_beads:
    	# mix
    	bead_mix(pipette,
            	 plate,
            	 cols,
            	 mix_tiprack,
            	 n=mix_n,
            	 mix_vol=mix_vol,
            	 drop_tip=drop_mix_tip,
            	 z_offset=mix_z_offset,
                 mix_lift=mix_lift)

    	# engage magnet
    	if mag_engage_height is not None:
        	magblock.engage(height_from_base=mag_engage_height)
    	else:
        	magblock.engage()

    	protocol.delay(seconds=pause_s)

    return(wash_wells, wash_remaining)


def transfer_elute(pipette,
                   source,
                   dest,
                   cols,
                   tiprack,
                   vol,
                   z_offset=0.5,
                   x_offset=1,
                   rate=0.25,
                   drop_tip=True,
                   mix_n=None,
                   mix_vol=None):

    for col in cols:
        # determine offset
        side = odd_or_even(col)
        offset = (-1)**side * x_offset

        center_loc = source[col].bottom(z=z_offset)
        offset_loc = center_loc.move(types.Point(x=offset,
                                                 y=0,
                                                 z=0))

        pipette.pick_up_tip(tiprack[col])
        pipette.aspirate(vol, offset_loc, rate=rate)
        pipette.dispense(vol, dest[col])

        if mix_n is not None:
            pipette.mix(mix_n,
                        mix_vol,
                        dest[col].bottom(z=1))
            pipette.blow_out(dest[col].top())
        if drop_tip:
            pipette.drop_tip()
        else:
            pipette.return_tip()
