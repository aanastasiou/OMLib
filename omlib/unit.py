from rdflib import Literal, XSD, URIRef

from exceptions.dimensionexception import DimensionalException
from exceptions.unitconversionexception import UnitConversionException
from omlib.dimension import Dimension
from omlib.thing import Thing, SymbolThing


class Unit(SymbolThing):
    _units = []

    @staticmethod
    def with_label(label):
        get_units = []
        for unit in Unit._units:
            for ulabel in unit.all_labels():
                if str(ulabel) == label:
                    get_units.append(unit)
        return get_units

    @staticmethod
    def with_symbol(symbol):
        get_units = []
        for unit in Unit._units:
            for usymbol in unit.all_symbols():
                if str(usymbol) == symbol:
                    get_units.append(unit)
        return get_units

    @staticmethod
    def with_identifier(identifier):
        for unit in Unit._units:
            if str(unit.identifier) == str(identifier):
                return unit
        return None

    @staticmethod
    def __add_unit(unit):
        duplicate = False
        if isinstance(unit.identifier, URIRef):
            if Unit.with_identifier(unit.identifier) is not None:
                duplicate = True
        print("Unit adding: {} duplicate: {}".format(unit, duplicate))
        if not duplicate:
            Unit._units.append(unit)

    @staticmethod
    def conversion_factor(from_unit, to_unit):
        can_convert = Unit.can_covert(from_unit, to_unit)
        if not can_convert:
            raise DimensionalException("A unit with dimensions {} cannot be converted to a unit with dimensions {}."
                                       .format(from_unit.dimensions, to_unit.dimensions))
        from_to_base_ancestor = from_unit.first_ancestor()
        to_to_base_ancestor = to_unit.first_ancestor()
        if str(from_to_base_ancestor[0].identifier) == str(to_to_base_ancestor[0].identifier):
            return from_to_base_ancestor[1] / to_to_base_ancestor[1]
        raise UnitConversionException("Cannot convert from {} to {} as they do not have a common ancestor unit."
                                      .format(from_unit, to_unit))

    @staticmethod
    def can_covert(from_unit, to_unit):
        if isinstance(from_unit, Unit) and isinstance(to_unit, Unit):
            if from_unit.dimensions == to_unit.dimensions:
                return True
            return False
        if not isinstance(from_unit, Unit) and not isinstance(to_unit, Unit):
            raise ValueError("Both arguments of can_convert are required to be of type Unit.")
        if not isinstance(from_unit, Unit):
            raise ValueError("The first argument of can_convert is required to be of type Unit.")
        if not isinstance(to_unit, Unit):
            raise ValueError("The second argument of can_convert is required to be of type Unit.")

    @staticmethod
    def get_singular_unit(label, symbol, dimensions=Dimension(), base_unit=None, factor=1.0, identifier=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            unit = SingularUnit(label, symbol, dimensions, base_unit, factor, identifier)
            Unit.__add_unit(unit)
        return unit

    @staticmethod
    def get_prefixed_unit(prefix, base_unit, identifier=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            unit = PrefixedUnit(prefix, base_unit, identifier)
            Unit.__add_unit(unit)
        return unit

    @staticmethod
    def get_unit_multiple(base_unit, factor=1.0, identifier=None, label=None, symbol=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            unit = UnitMultiple(base_unit, factor, identifier, label, symbol)
            Unit.__add_unit(unit)
        return unit

    @staticmethod
    def get_unit_multiplication(multiplier, multiplicand, symbol=None, identifier=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            for unit in Unit._units:
                if isinstance(unit, UnitMultiplication):
                    if str(multiplier.identifier) == str(unit.multiplier.identifier) and \
                            str(multiplicand.identifier) == str(unit.multiplicand.identifier):
                        return unit
            unit = UnitMultiplication(multiplier, multiplicand, symbol, identifier)
            Unit.__add_unit(unit)
        return unit

    @staticmethod
    def get_unit_division(numerator, denominator, symbol=None, identifier=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            for unit in Unit._units:
                if isinstance(unit, UnitDivision):
                    if str(numerator.identifier) == str(unit.numerator.identifier) and \
                            str(denominator.identifier) == str(unit.denominator.identifier):
                        return unit
            unit = UnitDivision(numerator, denominator, symbol, identifier)
            Unit.__add_unit(unit)
        return unit

    @staticmethod
    def get_unit_exponentiation(base, exponent, symbol=None, identifier=None):
        unit = None
        if identifier is not None:
            unit = Unit.with_identifier(identifier)
        if unit is None:
            for unit in Unit._units:
                if isinstance(unit, UnitExponentiation):
                    if str(base.identifier) == str(unit.base.identifier) and \
                            exponent == unit.exponent:
                        return unit
            unit = UnitExponentiation(base, exponent, symbol, identifier)
            Unit.__add_unit(unit)
        return unit

    def __init__(self, label=None, symbol=None, dimensions=Dimension(), identifier=None):
        super().__init__(label, symbol, identifier)
        self.dimensions = dimensions

    def __str__(self):
        return f'{self.label()}\t{self.symbol()}\t<{self.identifier}>  dim: {self.dimensions}'

    def first_ancestor(self):
        return self, 1.0


class Prefix(object):

    def __init__(self, name, symbol, factor):
        self.name = name
        self.symbol = symbol
        self.factor = factor


class SingularUnit(Unit):

    def __init__(self, label, symbol, dimensions=Dimension(), base_unit=None, factor=1.0, identifier=None):
        if base_unit is not None:
            dimensions = base_unit.dimensions
        super().__init__(label, symbol, dimensions, identifier)
        self.factor = factor
        self.baseUnit = base_unit

    def first_ancestor(self):
        if self.baseUnit is None:
            return self, 1.0
        first_ancestor = self.baseUnit.first_ancestor()
        return first_ancestor[0], first_ancestor[1] * self.factor


class PrefixedUnit(Unit):
    def __init__(self, prefix, base_unit, identifier=None):
        label = f'{prefix.name}{base_unit.label()}'
        symbol = f'{prefix.symbol}{base_unit.symbol()}'
        self.prefix = prefix
        self.baseUnit = base_unit
        super().__init__(label, symbol, dimensions=self.baseUnit.dimensions, identifier=identifier)

    def first_ancestor(self):
        if self.baseUnit is None:
            return self, 1.0
        first_ancestor = self.baseUnit.first_ancestor()
        return first_ancestor[0], first_ancestor[1] * self.prefix.factor


class UnitMultiple(SingularUnit):

    def __init__(self, base_unit, factor=1.0, identifier=None, label=None, symbol=None):
        if label is None:
            label = f'{factor} {base_unit.label()}'
        if symbol is None:
            symbol = f'{factor}{base_unit.symbol()}'
        super().__init__(label, symbol, base_unit.dimensions, base_unit, factor, identifier)


class CompoundUnit(Unit):

    def __init__(self, symbol, dimensions, identifier=None):
        super().__init__(None, symbol, dimensions, identifier)


class UnitMultiplication(CompoundUnit):

    def __init__(self, multiplier, multiplicand, symbol=None, identifier=None):
        dimensions = multiplier.dimensions * multiplicand.dimensions
        if symbol is None:
            multiplier_str = str(multiplier.symbol())
            if isinstance(multiplier, CompoundUnit):
                multiplier_str = f'({multiplier_str})'
            multiplicand_str = str(multiplicand.symbol())
            if isinstance(multiplicand, CompoundUnit):
                multiplicand_str = f'({multiplicand_str})'
            symbol = f'{multiplier_str}.{multiplicand_str}'
        super().__init__(symbol, dimensions, identifier)
        self.multiplier = multiplier
        self.multiplicand = multiplicand

    def first_ancestor(self):
        first_ancestor_multiplier = self.multiplier.first_ancestor()
        first_ancestor_multiplicand = self.multiplicand.first_ancestor()
        first_ancestor = Unit.get_unit_multiplication(first_ancestor_multiplier[0], first_ancestor_multiplicand[0])
        return first_ancestor, first_ancestor_multiplier[1] * first_ancestor_multiplicand[1]


class UnitDivision(CompoundUnit):

    def __init__(self, numerator, denominator, symbol=None, identifier=None):
        dimensions = numerator.dimensions / denominator.dimensions
        if symbol is None:
            numerator_str = str(numerator.symbol())
            if isinstance(numerator, CompoundUnit):
                numerator_str = f'({numerator_str})'
            denominator_str = str(denominator.symbol())
            if isinstance(denominator, CompoundUnit):
                denominator_str = f'({denominator_str})'
            symbol = f'{numerator_str}/{denominator_str}'
        super().__init__(symbol, dimensions, identifier)
        self.numerator = numerator
        self.denominator = denominator

    def first_ancestor(self):
        first_ancestor_numerator = self.numerator.first_ancestor()
        first_ancestor_denominator = self.denominator.first_ancestor()
        first_ancestor = Unit.get_unit_multiplication(first_ancestor_numerator[0], first_ancestor_denominator[0])
        return first_ancestor, first_ancestor_numerator[1] / first_ancestor_denominator[1]


class UnitExponentiation(CompoundUnit):

    def __init__(self, base, exponent, symbol=None, identifier=None):
        dimensions = Dimension.pow(base.dimensions, exponent)
        if symbol is None:
            base_str = str(base.symbol())
            if isinstance(base, CompoundUnit):
                base_str = f'({base_str})'
            symbol = f'{base_str}{exponent}'
        super().__init__(symbol, dimensions, identifier)
        self.base = base
        self.exponent = exponent

    def first_ancestor(self):
        first_ancestor_base = self.base.first_ancestor()
        first_ancestor = Unit.get_unit_exponentiation(first_ancestor_base[0], self.exponent)
        return first_ancestor, pow(first_ancestor_base[1], self.exponent)
