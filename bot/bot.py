import random
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


class LTSMPBot(BotAI):
    NAME: str = "LTSMPBot"
    """Loose Terrifying Space Monkey Protoss Bot"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """

    attack_points = []

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        if iteration % 5 == 0:
            print(f"{iteration}, n_workers: {self.workers.amount}, n_idle_workers: {self.workers.idle.amount},", \
                  f"minerals: {self.minerals}, gas: {self.vespene}, cannons: {self.structures(UnitTypeId.PHOTONCANNON).amount},", \
                  f"pylons: {self.structures(UnitTypeId.PYLON).amount}, nexus: {self.structures(UnitTypeId.NEXUS).amount}", \
                  f"gateways: {self.structures(UnitTypeId.GATEWAY).amount}, \n cybernetics cores: {self.structures(UnitTypeId.CYBERNETICSCORE).amount}", \
                  f"stargates: {self.structures(UnitTypeId.STARGATE).amount}, "
                  f"voidrays: {self.units(UnitTypeId.VOIDRAY).amount}, supply: {self.supply_used}/{self.supply_cap}, "
                  f"shield_upgrade1: {self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1)}, air_weap_upgrade1: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)}, air_arm_upgrade1: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1)} "
                  f"shield_upgrade2: {self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL2)}, air_weap_upgrade2: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)}, air_arm_upgrade2: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL2)} "
                  f"shield_upgrade3: {self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL3)}, air_weap_upgrade3: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)}, air_arm_upgrade3: {self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL3)} ")

        await self.distribute_workers()

        # begin basic logic
        if self.townhalls:  # do we have a Nexus?
            nexus = self.townhalls.random  # select a Town Hall at random
            #  nexus.tag .closest(UnitTypeId.MINERALFIELD)
            if nexus.surplus_harvesters >= -3 and not self.already_pending(UnitTypeId.NEXUS) \
                    and self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()  # build a nexus
            # else:
            # if we have less than x void rays, build one:
            if self.can_afford(UnitTypeId.VOIDRAY):
                for sg in self.structures(UnitTypeId.STARGATE).ready.idle:
                    if self.can_afford(UnitTypeId.VOIDRAY):
                        sg.train(UnitTypeId.VOIDRAY)

            # leave room to build void rays
            supply_remaining = self.supply_cap - self.supply_used
            if nexus.is_idle and self.can_afford(UnitTypeId.PROBE) \
                    and supply_remaining > 4 and nexus.surplus_harvesters < 1:
                nexus.train(UnitTypeId.PROBE)  # train a probe

            elif not self.structures(UnitTypeId.PYLON) and not self.already_pending(UnitTypeId.PYLON) \
                    and self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=self.main_base_ramp.protoss_wall_pylon)

            elif self.structures(UnitTypeId.PYLON) and not self.already_pending(UnitTypeId.PYLON) \
                    and self.can_afford(UnitTypeId.PYLON) and supply_remaining <= 4:
                for struct in self.structures.filter(lambda unit: unit.is_powered is False):
                    target_pylon = self.structures(UnitTypeId.PYLON).closest_to(struct)
                if not target_pylon:
                    if self.structures(UnitTypeId.PYLON).amount < 5:
                        # build from the closest pylon towards the enemy to start
                        target_pylon = self.structures(UnitTypeId.NEXUS).closest_to(self.enemy_start_locations[0])
                    else:
                        target_pylon = self.structures(UnitTypeId.PYLON).random
                # build as far away from target_pylon as possible:
                pos = target_pylon.position.towards_with_random_angle(self.enemy_start_locations[0],
                                                                      random.randrange(8, 15))
                # pos = target_pylon.position.towards(self.enemy_start_locations[0], random.randrange(8, 15))
                await self.build(UnitTypeId.PYLON, near=pos)

            # need an additional one based on number of nexus' and if you can afford an Assimilator
            elif self.structures(UnitTypeId.ASSIMILATOR).amount < (
                    self.structures(UnitTypeId.NEXUS).amount * 2) and not self.already_pending(
                UnitTypeId.ASSIMILATOR) and self.can_afford(UnitTypeId.ASSIMILATOR):
                # if there are fewer number of Assimilator and there isn't one already pending
                for nexus in self.structures(UnitTypeId.NEXUS):
                    vespenes = self.vespene_geyser.closer_than(15, nexus)
                    for vespene in vespenes:
                        await self.build(UnitTypeId.ASSIMILATOR, vespene)  # build one near the nexus
            # a gateway? this gets us towards cyb core > stargate > void ray
            elif not self.structures(UnitTypeId.GATEWAY) and not self.already_pending(
                    UnitTypeId.GATEWAY) and self.can_afford(UnitTypeId.GATEWAY):
                await self.build(UnitTypeId.GATEWAY,
                                 near=self.main_base_ramp.protoss_wall_buildings[0])

            # a cyber core? this gets us towards stargate > void ray
            elif not self.structures(UnitTypeId.CYBERNETICSCORE) and not self.already_pending(
                    UnitTypeId.CYBERNETICSCORE) and self.can_afford(UnitTypeId.CYBERNETICSCORE):
                await self.build(UnitTypeId.CYBERNETICSCORE,
                                 near=self.main_base_ramp.protoss_wall_buildings[1])

            # a stargate? this gets us towards void ray if we haven't built one yet or there is one and none are idle
            elif not self.already_pending(UnitTypeId.STARGATE) and (
                    not self.structures(UnitTypeId.STARGATE) and self.can_afford(UnitTypeId.STARGATE)
                    and self.structures(UnitTypeId.CYBERNETICSCORE).ready) \
                    or (self.structures(UnitTypeId.STARGATE)
                        and len(self.structures(UnitTypeId.STARGATE).ready.idle) == 0):
                await self.build(UnitTypeId.STARGATE,
                                 near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRWEAPONSLEVEL1) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) == 0:
                self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)
            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRARMORSLEVEL1) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1) == 0:
                self.research(UpgradeId.PROTOSSAIRARMORSLEVEL1)

            # if we don't have a fleet beacon and we can afford one:
            elif not self.structures(UnitTypeId.FLEETBEACON) and not self.already_pending(
                    UnitTypeId.FLEETBEACON) and self.can_afford(UnitTypeId.FLEETBEACON) \
                    and self.structures(UnitTypeId.CYBERNETICSCORE).ready \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) > 0.75 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1) > 0.75:
                #  build a fleet beacon!
                await self.build(UnitTypeId.FLEETBEACON, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            # TODO Flux Vanes Upgrade
            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRWEAPONSLEVEL2) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL1) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 0 \
                    and self.structures(UnitTypeId.FLEETBEACON).ready:
                self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)
            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRWEAPONSLEVEL3) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL2) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRWEAPONSLEVEL3) == 0 \
                    and self.structures(UnitTypeId.FLEETBEACON).ready:
                self.research(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)

            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRARMORSLEVEL2) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL1) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 0 \
                    and self.structures(UnitTypeId.FLEETBEACON).ready:
                self.research(UpgradeId.PROTOSSAIRARMORSLEVEL2)
            elif self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(
                    UpgradeId.PROTOSSAIRARMORSLEVEL3) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL2) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSAIRARMORSLEVEL3) == 0 \
                    and self.structures(UnitTypeId.FLEETBEACON).ready:
                self.research(UpgradeId.PROTOSSAIRARMORSLEVEL3)

            # if we don't have a forge and we can afford one:
            elif not self.structures(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE) \
                    and self.can_afford(UnitTypeId.FORGE):
                #  build a forge!
                await self.build(UnitTypeId.FORGE, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            elif self.structures(UnitTypeId.FORGE).ready and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL1) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1) == 0:
                self.research(UpgradeId.PROTOSSSHIELDSLEVEL1)

            # if we don't have a twilight council and we can afford one:
            elif not self.structures(UnitTypeId.TWILIGHTCOUNCIL) and not self.already_pending(
                    UnitTypeId.TWILIGHTCOUNCIL) \
                    and self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and self.structures(UnitTypeId.FORGE).ready \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1) > 0.75:
                #  build a twilight council!
                await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))
            elif self.structures(UnitTypeId.FORGE).ready and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL2) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL2) == 0 \
                    and self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
                self.research(UpgradeId.PROTOSSSHIELDSLEVEL2)
            elif self.structures(UnitTypeId.FORGE).ready and self.can_afford(UpgradeId.PROTOSSSHIELDSLEVEL3) \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL2) == 1 \
                    and self.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL3) == 0 \
                    and self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
                self.research(UpgradeId.PROTOSSSHIELDSLEVEL3)
            # if there are less than 3 cannons, build more
            elif self.structures(UnitTypeId.FORGE).ready and self.structures(UnitTypeId.PHOTONCANNON).amount < (
                    self.structures(UnitTypeId.NEXUS).amount * 3) \
                    and self.can_afford(UnitTypeId.PHOTONCANNON) \
                    and not self.already_pending(UnitTypeId.PHOTONCANNON) \
                    and self.minerals > 1500:
                #  the forge is ready and we have less than 3 cannons
                await self.build(UnitTypeId.PHOTONCANNON, near=nexus)  # build them near the nexus

        else:  # there isn't a nexus - this is a priority to reestablish a nexus
            if self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()  # build a nexus

        # if we have more than 3 VoidRays, let's attack!
        if (1 <= self.units(UnitTypeId.VOIDRAY).amount <= 5
            and self.time < 360) or (
                self.units(UnitTypeId.VOIDRAY).amount >= 10):
            attack_set = set(self.enemy_start_locations + self.expansion_locations_list).difference(
                self.attack_points)
            if len(attack_set) <= 1:
                self.attack_points = []
            attack_point = attack_set.pop()
            for vr in self.units(UnitTypeId.VOIDRAY).idle:
                if self.enemy_units:
                    vr.attack(random.choice(self.enemy_units))
                elif self.enemy_structures:
                    vr.smart(random.choice(self.enemy_structures))
                elif len(self.attack_points) == 0:
                    # otherwise attack enemy starting position
                    vr.smart(self.enemy_start_locations[0])
                    self.attack_points.append(self.enemy_start_locations[0])
                else:
                    vr.smart(attack_point)
                    self.attack_points.append(attack_point)

        else:
            for vr in self.units(UnitTypeId.VOIDRAY).idle:
                vr.move(self.main_base_ramp.top_center)

    async def on_end(self, result: Result):  # test
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
