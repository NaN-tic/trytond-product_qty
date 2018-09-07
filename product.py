# This file is part product_qty module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Template', 'Product']


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    def sum_product(self, name):
        Location = Pool().get('stock.location')

        if (name in ('quantity', 'forecast_quantity') and
                'locations' not in Transaction().context):
            warehouses = Location.search([('type', '=', 'warehouse')])
            location_ids = [w.storage_location.id for w in warehouses]
            with Transaction().set_context(locations=location_ids,
                    with_childs=True):
                return super(Template, self).sum_product(name)
        return super(Template, self).sum_product(name)


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    @classmethod
    def get_quantity(cls, products, name):
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
                    stock_date_end=today, with_childs=True):
                products_ids = map(int, products)
                return cls._get_quantity(products, name, location_ids,
                    grouping_filter=(products_ids,))
        # return super (with locations in context)
        return super(Product, cls).get_quantity(products, name)

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
        return super(Product, cls).search_quantity(name, domain)
