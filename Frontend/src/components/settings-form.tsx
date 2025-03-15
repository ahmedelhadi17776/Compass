"use client"

import React, { useState } from 'react';
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { X } from "lucide-react"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/useAuth"

interface SettingsFormProps {
  onClose: () => void
}

const formSchema = z.object({
  first_name: z.string().min(2, "First name must be at least 2 characters"),
  last_name: z.string().min(2, "Last name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
})

const SettingsForm: React.FC<SettingsFormProps> = ({ onClose }) => {
  const { user, updateUser } = useAuth()
  const [isClosing, setIsClosing] = useState(false)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      email: user?.email || "",
    },
  })

  const handleClose = () => {
    setIsClosing(true)
    setTimeout(() => onClose(), 300)
  }

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      await updateUser.mutateAsync(values)
      handleClose()
    } catch (error) {
      console.error('Failed to update settings:', error)
    }
  }

  return (
    <div className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 
      ${isClosing ? 'animate-fade-out' : 'animate-fade-in'}`}
    >
      <div className={`bg-[#1a1a1a] rounded-lg shadow-xl w-full max-w-md p-6 relative
        ${isClosing ? 'animate-slide-out' : 'animate-slide-in'}`}
      >
        <button
          onClick={handleClose}
          className="absolute right-4 top-4 text-[#a0a0a0] hover:text-[#e5e5e5]"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-xl font-semibold text-[#e5e5e5] mb-6">Settings</h2>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="block text-sm font-medium text-[#e5e5e5]">First Name</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        className="mt-1 block w-full rounded-md bg-[#1a1a1a] border-[#e7e7e7] text-[#e5e5e5] shadow-sm focus:border-[#e7e7e7] focus:ring-[#e7e7e7]"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="block text-sm font-medium text-[#e5e5e5]">Last Name</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        className="mt-1 block w-full rounded-md bg-[#1a1a1a] border-[#e7e7e7] text-[#e5e5e5] shadow-sm focus:border-[#e7e7e7] focus:ring-[#e7e7e7]"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="block text-sm font-medium text-[#e5e5e5]">Email</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      className="mt-1 block w-full rounded-md bg-[#1a1a1a] border-[#e7e7e7] text-[#e5e5e5] shadow-sm focus:border-[#e7e7e7] focus:ring-[#e7e7e7]"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3 mt-6">
              <Button
                type="button"
                onClick={handleClose}
                variant="outline"
                className="px-4 py-2 border-[#e7e7e7] text-[#e5e5e5] hover:bg-[#e7e7e7] hover:text-[#1a1a1a]"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateUser.isPending}
                className="px-4 py-2 bg-[#e7e7e7] text-[#1a1a1a] hover:bg-[#f0f0f0]"
              >
                {updateUser.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </Form>
      </div>
    </div>
  )
}

export default SettingsForm