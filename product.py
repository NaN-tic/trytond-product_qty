# This file is part product_qty module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import datetime
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    @classmethod
    def get_quantity(cls, products, name):
        pool = Pool()
        Location = pool.get('stock.location')
        Date = pool.get('ir.date')

        stock_date = Date.today() if name == 'product' else datetime.date.max
        context = Transaction().context

        # not locations in context
        if not context.get('locations'):
            warehouses = Location.search([('type', '=', 'warehouse')])
            location_ids = [w.storage_location.id for w in warehouses]
            with Transaction().set_context(locations=location_ids,
                    stock_date_end=stock_date, with_childs=True):
                products_ids = list(map(int, products))
                return cls._get_quantity(products, name, location_ids,
                    grouping_filter=(products_ids,))
        # return super (with locations in context)
        return super().get_quantity(products, name)

    @classmethod
    def search_quantity(cls, name, domain=None):
        pool = Pool()
        Location = pool.get('stock.location')
        Date = pool.get('ir.date')

        today = Date.today()
        context = Transaction().context
        # not locations in context
        if not context.get('locations'):
            warehouses = Location.search([('type', '=', 'warehouse')])
            location_ids = [w.storage_location.id for w in warehouses]
            with Transaction().set_context(locations=location_ids,
                    stock_date_end=today):
                return cls._search_quantity(name, location_ids, domain)
        # return super (with locations in context)
        return super().search_quantity(name, domain)
