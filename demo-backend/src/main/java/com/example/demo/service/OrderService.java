package com.example.demo.service;

import com.example.demo.entity.Order;
import java.util.List;

public interface OrderService {
    
    Order findById(Long id);
    
    List<Order> findByUserId(Long userId);
    
    List<Order> findAll();
    
    Order create(Order order);
    
    Order update(Order order);
    
    void delete(Long id);
}
