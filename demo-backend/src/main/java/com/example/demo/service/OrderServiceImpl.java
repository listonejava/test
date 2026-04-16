package com.example.demo.service;

import com.example.demo.entity.Order;
import com.example.demo.mapper.OrderMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class OrderServiceImpl implements OrderService {
    
    @Autowired
    private OrderMapper orderMapper;
    
    @Override
    public Order findById(Long id) {
        return orderMapper.findById(id);
    }
    
    @Override
    public List<Order> findByUserId(Long userId) {
        return orderMapper.findByUserId(userId);
    }
    
    @Override
    public List<Order> findAll() {
        return orderMapper.findAll();
    }
    
    @Override
    public Order create(Order order) {
        orderMapper.insert(order);
        return order;
    }
    
    @Override
    public Order update(Order order) {
        orderMapper.update(order);
        return order;
    }
    
    @Override
    public void delete(Long id) {
        orderMapper.deleteById(id);
    }
}
