package com.example.demo.mapper;

import com.example.demo.entity.Order;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

@Mapper
public interface OrderMapper {
    
    Order findById(@Param("id") Long id);
    
    List<Order> findByUserId(@Param("userId") Long userId);
    
    List<Order> findAll();
    
    int insert(Order order);
    
    int update(Order order);
    
    int deleteById(@Param("id") Long id);
}
